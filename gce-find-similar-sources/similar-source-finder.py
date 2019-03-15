import os
import time
from contextlib import suppress
from tempfile import gettempdir

import requests
from google.cloud import storage
from google.cloud import pubsub
import pandas as pd

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
SOURCES_BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-detected-sources')
PSC_BUCKET_NAME = os.getenv('UPLOAD_BUCKET', 'panoptes-observation-psc')
storage_client = storage.Client(project=PROJECT_ID)
sources_bucket = storage_client.get_bucket(SOURCES_BUCKET_NAME)
psc_bucket = storage_client.get_bucket(PSC_BUCKET_NAME)

# Pubsub
PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'gce-find-similar-sources')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'


update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)


def main():
    print(f"Starting similar source finder on {pubsub_sub_path}")

    try:
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            pubsub_sub_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        print(f"Similar source finder subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        print(f'Problem starting subscriber: {e!r}')
        future.cancel()


def msg_callback(message):

    attributes = message.attributes
    sequence_id = attributes['sequence_id']

    # Put sequence_id into path form.
    sequence_id = sequence_id.replace('_', '/')

    # Strip trailing slash
    if sequence_id.endswith('/'):
        sequence_id = sequence_id[:-1]

    # The output file that will contain the similar source list.
    similar_sources_fn = f'{sequence_id}-similar-sources.csv'

    # The local path to the similar source list.
    local_similar_sources_path = os.path.join('/tmp', similar_sources_fn.replace('/', '_'))

    # Create the observation PSC
    try:
        psc_df = make_observation_psc(**attributes)
        if psc_df is None:
            raise Exception(f'Sequence ID: {sequence_id} No PSC created')
    except Exception as e:
        print(f'Error making PSC: {e!r}')
        message.ack()
        return

    print(f'Sequence ID: {sequence_id} Done creating PSC, finding similar sources.')

    try:
        similar_sources = find_similar_sources(psc_df, sequence_id)

        print(f'Making {local_similar_sources_path}')
        similar_sources.to_csv(local_similar_sources_path)

        upload_blob(local_similar_sources_path, similar_sources_fn, bucket=psc_bucket)
    finally:
        print(f'Finished processing {sequence_id}.')
        message.ack()
        return


def make_observation_psc(sequence_id, min_num_frames=10, frame_threshold=0.98, **kwargs):
    """Makes a PSC dataframe for the given sequence id.

    Args:
        sequence_id (str): The sequence_id in the form `<unit_id>_<camera_id>_<sequence_time>`.
        For convenience the `_` can be replaced with `/`.


    Returns:
        `pandas.DataFrame`: Dataframe of the PSC.
    """
    print(f'Sequence ID: {sequence_id} Making PSC')

    bucket_path = sequence_id.replace('_', '/')
    # Add trailing slash for lookups
    if bucket_path.endswith('/') is False:
        bucket_path = f'{bucket_path}/'
    print(f'Getting CSV files in bucket: {bucket_path}')
    csv_blobs = sources_bucket.list_blobs(prefix=bucket_path, delimiter='/')

    # Add the CSV files one at a time.
    df_list = dict()
    try:
        for blob in csv_blobs:
            print(f'Getting blob name {blob.name}')
            tmp_fn = os.path.join(gettempdir(), blob.name.replace('/', '_'))
            print(f'Downloading to {tmp_fn}')
            blob.download_to_filename(tmp_fn)

            print(f'Making DataFrame for {tmp_fn}')
            df0 = pd.read_csv(tmp_fn)

            # Make a datetime index
            df0.index = pd.to_datetime(df0.image_time)
            df0.drop(columns=['image_time'])

            # Cleanup columns
            df0.drop(columns=['unit_id', 'camera_id', 'sequence_time', 'image_time'], inplace=True)
            df_list[tmp_fn] = df0

        if len(df_list) <= min_num_frames:
            state = 'error_seq_too_short'
            requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
            print(f'Not enough CSV files found for {sequence_id}: {len(df_list)} files found')
            return None

        print(f'Making PSC DataFrame for {sequence_id}')
        psc_df = pd.concat(list(df_list.values()), sort=False)

        # Only keep the keys (filenames)
        df_list = list(df_list.keys())

        # Make the PICID (as str) an index
        psc_df.picid = psc_df.picid.astype(str)
        psc_df.set_index(['picid'], inplace=True, append=True)
        psc_df.sort_index(inplace=True)

        # Report
        num_sources = len(psc_df.index.levels[1].unique())
        num_frames = len(set(psc_df.index.levels[0].unique()))
        print(f"Sequence: {sequence_id} Frames: {num_frames} Sources: {num_sources}")

        # Get minimum frame threshold
        frame_count = psc_df.groupby('picid').count().pixel_00
        min_frame_count = int(frame_count.max() * frame_threshold)
        print(f'Sequence: {sequence_id} Frames: {frame_count.max()} Min cutout: {min_frame_count}')

        # Filter out the sources where the number of frames is less than min_frame_count
        def has_frame_count(grp):
            return grp.count()['pixel_00'] >= min_frame_count

        # Do the actual fileter an reset the index
        print(f'Sequence: {sequence_id} filtering sources')
        psc_df = psc_df.reset_index() \
            .groupby('picid') \
            .filter(has_frame_count) \
            .set_index(['image_time', 'picid'])

        # Report again
        num_sources = len(psc_df.index.levels[1].unique())
        num_frames = len(set(psc_df.index.levels[0].unique()))
        print(f"Frames: {num_frames} Sources: {num_sources}")

        # Write to file
        out_fn = sequence_id.replace('/', '_')
        if out_fn.endswith('_'):
            out_fn = out_fn[:-1]
        out_fn = os.path.join(gettempdir(), f'{out_fn}.csv')
        print(f'Writing DataFrame to {out_fn}')
        psc_df.to_csv(out_fn)

        upload_bucket_path = f'{sequence_id}.csv'.replace('_', '/')

        print(f'Uploading {out_fn} to {upload_bucket_path}')
        upload_blob(out_fn, upload_bucket_path)

        print(f'Removing {out_fn}')
        os.remove(out_fn)

        state = 'psc_created'
        print(f'Updating state for {sequence_id} to {state}')
        requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})

    finally:
        print(f'Removing all downloaded files for {sequence_id}')
        for tmp_fn in df_list:
            with suppress(FileNotFoundError):
                os.remove(tmp_fn)

    print(f"PSC file created for {sequence_id}")
    return psc_df


def find_similar_sources(stamps_df, sequence_id):
    print(f'Loading PSC CSV for {sequence_id}')

    # Normalize each stamp
    print(f'Normalizing PSC for {sequence_id}')
    norm_df = stamps_df.copy().apply(lambda x: x / stamps_df.sum(axis=1))

    top_matches = dict()
    print(f'Starting loop of PSCs for {sequence_id}')
    for picid, row in norm_df.groupby('picid'):
        norm_target = row.droplevel('picid')
        norm_group = ((norm_df - norm_target)**2).dropna().sum(axis=1).groupby('picid')
        top_matches[picid] = norm_group.sum().sort_values()

    print(f'Making DataFrame of similar sources for {sequence_id}')
    similar_sources = pd.DataFrame(top_matches)

    return similar_sources


def download_blob(source_blob_name, destination=None, bucket=None, bucket_name='panoptes-survey'):
    """Downloads a blob from the bucket."""
    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(source_blob_name)

    # If no name then place in current directory
    if destination is None:
        destination = source_blob_name.replace('/', '_')

    if os.path.isdir(destination):
        destination = os.path.join(destination, source_blob_name.replace('/', '_'))

    blob.download_to_filename(destination)

    print('Blob {} downloaded to {}.'.format(source_blob_name, destination))

    return destination


def upload_blob(source_file_name, destination, bucket=None, bucket_name='panoptes-survey'):
    """Uploads a file to the bucket."""
    print('Uploading {} to {}.'.format(source_file_name, destination))

    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination))


if __name__ == '__main__':
    main()
