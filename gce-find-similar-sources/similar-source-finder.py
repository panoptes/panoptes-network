import os
import time
from datetime.datetime import now
from contextlib import suppress

import requests
from google.cloud import storage
from google.cloud import pubsub
from tqdm import tqdm
import pandas as pd

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
SOURCES_BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-detected-sources')
OBSERVATION_BUCKET_NAME = os.getenv('UPLOAD_BUCKET', 'panoptes-observation-psc')
storage_client = storage.Client(project=PROJECT_ID)

observation_bucket = storage_client.get_bucket(OBSERVATION_BUCKET_NAME)

# Pubsub
PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'gce-find-similar-sources')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'


update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)


def main():
    log(f"Starting similar source finder on {pubsub_sub_path}")

    try:
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            pubsub_sub_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        log(f"Similar source finder subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        log(f'Problem starting subscriber: {e!r}')
        future.cancel()


def log(msg):
    print(now().isoformat(), msg)


def msg_callback(message):

    attributes = message.attributes
    sequence_id = attributes['sequence_id']

    # Put sequence_id into path form.
    sequence_id = sequence_id.replace('_', '/')

    # Strip trailing slash
    if sequence_id.endswith('/'):
        sequence_id = sequence_id[:-1]

    # Create the observation PSC
    try:
        psc_df = make_observation_psc_df(**attributes)
        if psc_df is None:
            raise Exception(f'Sequence ID: {sequence_id} No PSC created')
    except Exception as e:
        log(f'Error making PSC: {e!r}')
        message.ack()
        return

    log(f'Sequence ID: {sequence_id} Done creating PSC, finding similar sources.')

    try:
        similar_sources = find_similar_sources(psc_df, sequence_id)

        # The output file that will contain the similar source list.
        bucket_path = f'gs://{OBSERVATION_BUCKET_NAME}/{sequence_id}-similar-sources.csv'
        log(f'Saving to {bucket_path}')
        similar_sources.to_csv(bucket_path)
    finally:
        log(f'Finished processing {sequence_id}.')
        message.ack()
        return


def make_observation_psc_df(sequence_id, min_num_frames=10, frame_threshold=0.98, **kwargs):
    """Makes a PSC dataframe for the given sequence id.

    Args:
        sequence_id (str): The sequence_id in the form `<unit_id>_<camera_id>_<sequence_time>`.
        For convenience the `_` can be replaced with `/`.


    Returns:
        `pandas.DataFrame`: Dataframe of the PSC.
    """
    log(f'Sequence ID: {sequence_id} Making PSC')

    sequence_id = sequence_id.replace('_', '/')

    psc_fn = f'gs://{OBSERVATION_BUCKET_NAME}/{sequence_id}.csv'
    log(f'Getting Observation CSV file in bucket: {psc_fn}')

    log(f'Making DataFrame for {psc_fn}')
    psc_df = pd.read_csv(psc_fn, index_col=[
                         'image_time', 'picid'], parse_dates=True).sort_index()

    # Report
    num_sources = len(psc_df.index.levels[1].unique())
    num_frames = len(set(psc_df.index.levels[0].unique()))
    log(f"Sequence: {sequence_id} Frames: {num_frames} Sources: {num_sources}")

    if num_frames <= min_num_frames:
        state = 'error_seq_too_short'
        requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
        log(f'Not enough frames found for {sequence_id}: {num_frames} frames found')
        return None

    # Get minimum frame threshold
    frame_count = psc_df.groupby('picid').count().pixel_00
    min_frame_count = int(frame_count.max() * frame_threshold)
    log(f'Sequence: {sequence_id} Frames: {frame_count.max()} Min cutout: {min_frame_count}')

    # Filter out the sources where the number of frames is less than min_frame_count
    def has_frame_count(grp):
        return grp.count()['pixel_00'] >= min_frame_count

    # Do the actual fileter an reset the index
    log(f'Sequence: {sequence_id} filtering sources')
    psc_df = psc_df.reset_index() \
        .groupby('picid') \
        .filter(has_frame_count) \
        .set_index(['image_time', 'picid'])

    # Report again
    num_sources = len(psc_df.index.levels[1].unique())
    num_frames = len(set(psc_df.index.levels[0].unique()))
    log(f"Sequence: {sequence_id} Frames: {num_frames} Sources: {num_sources}")

    # Update state
    state = 'psc_created'
    log(f'Updating state for {sequence_id} to {state}')
    requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})

    log(f"PSC DataFrame created for {sequence_id}")
    return psc_df


def find_similar_sources(stamps_df, sequence_id):
    log(f'Loading PSC CSV for {sequence_id}')

    # Normalize each stamp
    log(f'Normalizing PSC for {sequence_id}')
    norm_df = stamps_df.copy().apply(lambda x: x / stamps_df.sum(axis=1))

    top_matches = dict()
    log(f'Starting loop of PSCs for {sequence_id}')
    for picid, row in tqdm(norm_df.groupby('picid')):
        norm_target = row.droplevel('picid')
        norm_group = ((norm_df - norm_target)**2).dropna().sum(axis=1).groupby('picid')
        top_matches[picid] = norm_group.sum()

    log(f'Making DataFrame of similar sources for {sequence_id}')
    similar_sources = pd.DataFrame(top_matches)

    return similar_sources


if __name__ == '__main__':
    main()
