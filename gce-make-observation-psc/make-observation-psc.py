#!/usr/bin/env python

import os
import time
import re
from datetime import datetime
from contextlib import suppress

import requests
from google.cloud import pubsub
from google.cloud import storage
import pandas as pd
import dask.dataframe as dd

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
OBSERVATION_BUCKET_NAME = os.getenv('UPLOAD_BUCKET', 'panoptes-observation-psc')
SOURCES_BUCKET_NAME = os.getenv('UPLOAD_BUCKET', 'panoptes-detected-sources')

# Storage
storage_client = storage.Client(project=PROJECT_ID)
observation_bucket = storage_client.get_bucket(OBSERVATION_BUCKET_NAME)
sources_bucket = storage_client.get_bucket(SOURCES_BUCKET_NAME)

# Pubsub
PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'make-observation-psc')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'

update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)


class InvalidPSC(Exception):
    """Custom exception used to control some of the flow"""
    pass


def main():
    log(f"Starting Observation PSC maker on {pubsub_sub_path}")

    while True:
        try:
            response = subscriber_client.pull(pubsub_sub_path,
                                              max_messages=3,
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

    log(f'Received sequence_id: {sequence_id} object_id: {object_id}')

    # Get a sequence ID if given a n object id.
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
    except InvalidPSC as e:
        log(f'Problem with PSC for {sequence_id}: {e!r}')
        return
    except Exception as e:
        log(f'Error making PSC: {e!r}')
        # Update state
        state = 'error_filtering_observation_psc'
        log(f'Updating state for {sequence_id} to {state}')
        requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
        return

    log(f'Sequence ID: {sequence_id} Done creating PSC, finding similar sources.')

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
        raise InvalidPSC('No sequence_id given')

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

            log(f'Checking existing Observation PSC for {sequence_id}')
            if 'sextractor_flags' in psc_df.columns:
                log(f'Returning Observation PSC for {sequence_id}')
                return psc_df
            else:
                del psc_df
                log(f'Missing columns in existing PSC, forcing new.')

    else:
        log(f'Forcing new observation PSC for {sequence_id}')

    log(f'Looking up files for {sequence_id}')
    blobs = sources_bucket.list_blobs(prefix=sequence_id)

    stamp_files = list()  # Helps with cleanup
    for blob in blobs:
        # Save to local /tmp dir
        remote_fn = blob.name.replace('/', '-')
        temp_fn = f'/tmp/{remote_fn}'
        stamp_files.append(temp_fn)
        blob.download_to_filename(temp_fn)

    # Combine all CSV files
    log(f'Making Dask DataFrame')
    psc_df = dd.read_csv('/tmp/*.csv', parse_dates=True).set_index('image_time').compute()

    # Report
    num_sources = len(psc_df.picid.unique())
    num_frames = len(set(psc_df.index.unique()))
    log(f"Sequence: {sequence_id} Frames: {num_frames} Sources: {num_sources}")

    if num_frames <= min_num_frames:
        state = 'error_seq_too_short'
        requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})
        log(f'Not enough frames found for {sequence_id}: {num_frames} frames found')
        raise InvalidPSC('Sequence too short')

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
    for fn in stamp_files:
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


if __name__ == '__main__':
    main()
