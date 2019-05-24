#!/usr/bin/env python

import os
import time
import re
import concurrent.futures
from itertools import zip_longest
from datetime import datetime
from contextlib import suppress

import requests
from google.cloud import pubsub
from google.cloud import storage
import numpy as np
import pandas as pd

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
OBSERVATION_BUCKET_NAME = os.getenv('UPLOAD_BUCKET', 'panoptes-observation-psc')
SOURCES_BUCKET_NAME = os.getenv('UPLOAD_BUCKET', 'panoptes-detected-sources')
PICID_BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-picid')

# Storage
storage_client = storage.Client(project=PROJECT_ID)
observation_bucket = storage_client.get_bucket(OBSERVATION_BUCKET_NAME)
sources_bucket = storage_client.get_bucket(SOURCES_BUCKET_NAME)
picid_bucket = storage_client.get_bucket(PICID_BUCKET_NAME)

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

    while True:
        try:
            response = subscriber_client.pull(pubsub_sub_path,
                                              max_messages=2,
                                              return_immediately=True)
        except Exception as e:
            log(f'Problem with pulling from subscriber: {e!r}')
        else:
            try:
                # Process first (and only) message
                message = response.received_messages[0]
                log(f"Received message, processing: {message.ack_id}")

                # Acknowledge immediately - resend pubsub on error below.
                subscriber_client.acknowledge(pubsub_sub_path, [message.ack_id])

                # Will block while processing.
                process_message(message.message)
                log(f"Message complete: {message.ack_id}")
            except IndexError:
                # No messages, sleep before looping again.
                time.sleep(30)


def log(msg):
    print(datetime.now().isoformat(), msg)


def process_message(message):

    attributes = message.attributes

    object_id = attributes['objectId']  # Comes from bucket event.
    sequence_id = attributes['sequence_id']

    force_new = attributes.get('force_new', False)

    log(f'Received sequence_id: {sequence_id} object_id: {object_id}')

    if sequence_id is None or sequence_id == '':
        log(f'No sequence_id found, looking for matching object_id')
        matches = re.fullmatch('(PAN.{3}[/_].*[/_]20.{6}T.{6}).csv', object_id)
        if matches is not None:
            sequence_id = matches.group(1)
            log(f'Matched object_id, setting sequence_id={sequence_id}')
        else:
            log(f'Invalid sequence_id and no object_id, exiting: {object_id}')
            return

    # Put sequence_id into path form.
    sequence_id = sequence_id.replace('_', '/')

    # Strip trailing slash
    if sequence_id.endswith('/'):
        sequence_id = sequence_id[:-1]

    # Create the observation PSC
    try:
        attributes['sequence_id'] = sequence_id
        full_df = make_observation_psc_df(**attributes)
        if full_df is None:
            raise Exception(f'Sequence ID: {sequence_id} No PSC created')
    except FileNotFoundError as e:
        log(f'File for {sequence_id} not found in bucket, skipping.')
        return
    except Exception as e:
        log(f'Error making PSC: {e!r}')
        # Update state
        state = 'error_filtering_observation_psc'
        log(f'Updating state for {sequence_id} to {state}')
        requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
        return

    log(f'Sequence ID: {sequence_id} Done creating PSC, finding similar sources.')

    try:
        psc_df = full_df.loc[:, 'pixel_00':]
        if find_similar_sources(psc_df, sequence_id, force_new=force_new):
            # Update state
            state = 'similar_sources_found'
            log(f'Updating state for {sequence_id} to {state}')
            requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
    except Exception as e:
        log(f'ERROR Sequence {sequence_id}: {e!r}')
    else:
        log(f'Finished processing {sequence_id}.')

    return


def make_observation_psc_df(sequence_id=None,
                            min_num_frames=10,
                            frame_threshold=0.95,
                            force_new=False,
                            **kwargs):
    """Makes a PSC dataframe for the given sequence id.

    Args:
        sequence_id (str): The sequence_id in the form `<unit_id>_<camera_id>_<sequence_time>`.
        For convenience the `_` can be replaced with `/`.


    Returns:
        `pandas.DataFrame`: Dataframe of the PSC.
    """
    if sequence_id is None:
        return

    log(f'Sequence ID: {sequence_id} Making PSC')

    sequence_id = sequence_id.replace('_', '/')
    master_csv_fn = f'{sequence_id}.csv'

    # Look for existing file.
    if force_new is False:
        psc_df_blob = observation_bucket.get_blob(master_csv_fn)
        if psc_df_blob and psc_df_blob.exists():
            log(f'Found existing Observation PSC for {sequence_id}')
            master_csv_fn = master_csv_fn.replace('/', '_')
            master_csv_fn = f'/tmp/{master_csv_fn}'

            log(f'Downloading Observation PSC for {sequence_id}')
            psc_df_blob.download_to_filename(master_csv_fn)
            psc_df = pd.read_csv(master_csv_fn,
                                 index_col=['image_time', 'picid'],
                                 parse_dates=True)
            log(f'Returning Observation PSC for {sequence_id}')
            return psc_df
    else:
        log(f'Forcing new observation PSC for {sequence_id}')

    log(f'Looking up files for {sequence_id}')
    blobs = sources_bucket.list_blobs(prefix=sequence_id)

    stamps = dict()
    for blob in blobs:
        # Save to local /tmp dir
        remote_fn = blob.name.replace('/', '-')
        temp_fn = f'/tmp/{remote_fn}'
        blob.download_to_filename(temp_fn)

        # Load dataframe
        df0 = pd.read_csv(temp_fn, index_col=['image_time', 'picid'], parse_dates=True)
        stamps[temp_fn] = df0

    log(f'Making DataFrame for {len(stamps)} files')
    psc_df = pd.concat(list(stamps.values()), sort=True)

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

    # Do the actual filter and reset the index
    log(f'Sequence: {sequence_id} filtering sources')
    psc_df = psc_df.reset_index() \
        .groupby('picid') \
        .filter(has_frame_count) \
        .set_index(['image_time', 'picid'])

    # Report again
    num_sources = len(psc_df.index.levels[1].unique())
    num_frames = len(set(psc_df.index.levels[0].unique()))
    log(f"Sequence: {sequence_id} Frames: {num_frames} Sources: {num_sources}")

    # Remove files
    for fn in stamps.keys():
        with suppress(FileNotFoundError):
            os.remove(fn)

    log(f"PSC DataFrame created for {sequence_id}")

    try:
        bucket_url = f'gs://{OBSERVATION_BUCKET_NAME}/{master_csv_fn}'
        log(f"Saving full CSV for {sequence_id} to {bucket_url}")
        psc_df.to_csv(bucket_url)
    except Exception as e:
        print(f'Problem saving master CSV file: {e!r}')

    return psc_df


def compare_stamps(params):
    import numpy as np

    try:
        target_params = params[0]
        call_params = params[1]

        picid = target_params[0]
        target_table = target_params[1]

        ref_table = call_params['all_psc']
        sequence_id = call_params['sequence_id']
        force_new = call_params['force_new']

        # Check if file already exists
        save_fn = f'{picid}/{sequence_id}-similar-sources.csv'
        if force_new is False and picid_bucket.get_blob(save_fn):
            raise FileExistsError('File already found in storage bucket')

        # Align index with target
        include_frames = ref_table.index.levels[0].isin(target_table.index.levels[0])
        # Get PSC for matching frames
        ref_table = np.array(ref_table.loc[include_frames])

        # norm_target = target_table.droplevel('picid')
        norm_group = ((ref_table - target_table)**2).dropna().sum(axis=1).groupby('picid')

        top_matches = (norm_group.sum() / norm_group.std()).sort_values()[:500]

        save_fn = f'gs://{PICID_BUCKET_NAME}/{picid}/{sequence_id}-similar-sources.csv'
        top_matches.index.name = 'picid'
        top_matches.to_csv(save_fn, header=['sum_ssd'])
    except FileExistsError:
        return False
    except ValueError:
        # Mismatched frames
        return False
    except Exception as e:
        # Don't want to spit out error in thread
        print(f'ERROR PICID {picid} Sequence {sequence_id} Normalize: {e!r}')
        return False
    else:
        return picid


def find_similar_sources(stamps_df, sequence_id, force_new=False):
    log(f'Finding similar sources for {sequence_id}')

    # Normalize each stamp
    log(f'Normalizing PSC for {sequence_id}')
    try:
        final_pixel = [c for c in stamps_df.columns if c.startswith('pixel')][-1]
        norm_df = stamps_df.loc[:, 'pixel_00':final_pixel].apply(
            lambda x: x / stamps_df.sum(axis=1))
    except Exception as e:
        raise e

    call_params = dict(
        all_psc=norm_df,
        sequence_id=sequence_id,
        force_new=force_new
    )

    log(f'Starting loop of PSCs for {sequence_id}')
    # Run everything in parallel.
    start_time = datetime.now()
    with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
        grouped_sources = norm_df.groupby('picid')

        params = zip_longest(grouped_sources, [], fillvalue=call_params)

        picids = np.array(list(executor.map(compare_stamps, params, chunksize=4))).astype(bool)
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        log(f'Found similar stars for {picids.sum()} sources in {total_time:.1f} seconds')

    log(f'Sequence {sequence_id}: finished PICID loop')
    return True


if __name__ == '__main__':
    main()
