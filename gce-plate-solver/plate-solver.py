#!/usr/bin/env python3

import os
import sys
import time
import tempfile

import requests

from google.cloud import storage
from google.cloud import pubsub
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.google.cloudsql import get_cursor
from panoptes.piaa.utils.sources import lookup_point_sources
from panoptes.piaa import pipeline


# Make sure we are running in a GCP environment.
if ((os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '') == '') and
        (os.environ.get('GOOGLE_COMPUTE_INSTANCE', '') == '')):
    print(f"Don't know how to authenticate, refusing to run.")
    sys.exit(1)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
storage_client = storage.Client(project=PROJECT_ID)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
bucket = storage_client.get_bucket(BUCKET_NAME)

PROCESSED_BUCKET_NAME = os.getenv('PROCESSED_BUCKET_NAME', 'panoptes-processed')
processed_bucket = storage_client.get_bucket(PROCESSED_BUCKET_NAME)

PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'solve-extract-match')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'

update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)

get_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/get-state'
)

# Maximum number of simultaneous messages to process
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 2)


def main():
    print(f"Starting pubsub listen on {pubsub_sub_path}")

    try:
        # max_messages means we only process one at a time.
        flow_control = pubsub.types.FlowControl(max_messages=MAX_MESSAGES)
        scheduler = ThreadScheduler()
        future = subscriber_client.subscribe(
            pubsub_sub_path,
            callback=msg_callback,
            flow_control=flow_control,
            scheduler=scheduler
        )

        # Keeps main thread from exiting.
        print(f"Plate-solver subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        print(f'Problem in message callback: {e!r}')
        future.cancel()
        subscriber_client.close()


def msg_callback(message):

    attributes = message.attributes
    bucket_path = attributes['bucket_path']
    object_id = attributes['object_id']
    subtract_background = attributes.get('subtract_background', True)
    force = attributes.get('force_new', False)

    print(f'Received message {message.message_id} for {bucket_path}')
    if force:
        print(f'Found force=True, forcing new plate solving')

    try:
        # Get DB cursors
        catalog_db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')
        metadata_db_cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')
    except Exception as e:
        message.nack()
        error_msg = f"Can't connect to Cloud SQL proxy: {e!r}"
        print(error_msg)
        raise Exception(error_msg)

    print(f'Creating temporary directory for {bucket_path}')
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
        print(f'Solving {bucket_path}')
        try:
            solve_file(bucket_path,
                       object_id,
                       catalog_db_cursor,
                       metadata_db_cursor,
                       subtract_background=subtract_background,
                       force=force,
                       tmp_dir=tmp_dir_name
                       )
            print(f'Finished processing {bucket_path}.')
        except Exception as e:
            print(f'Problem with solve file: {e!r}')
            raise Exception(f'Problem with solve file: {e!r}')
        else:
            # Acknowledge message
            print(f'Acknowledging message {message.message_id} for {bucket_path}')
            message.ack()
        finally:
            catalog_db_cursor.close()
            metadata_db_cursor.close()

            print(f'Cleaning up temporary directory: {tmp_dir_name} for {bucket_path}')


def solve_file(bucket_path,
               object_id,
               catalog_db_cursor,
               metadata_db_cursor,
               subtract_background=True,
               force=False,
               tmp_dir='/tmp'):
    try:
        unit_id, field, cam_id, seq_time, file = bucket_path.split('/')
        img_time = file.split('.')[0]
        image_id = f'{unit_id}_{cam_id}_{img_time}'
    except Exception as e:
        raise Exception(f'Invalid file, skipping {bucket_path}: {e!r}')

    # Don't process pointing images.
    if 'pointing' in bucket_path:
        print(f'Skipping pointing file: {image_id}')
        update_state('skipped', image_id=image_id)
        return

    # Don't process files that have been processed.
    if (force is False) and (get_state(image_id=image_id) == 'sources_extracted'):
        print(f'Skipping already processed image: {image_id}')
        return

    try:  # Wrap everything so we can do file cleanup
        # Download file blob from bucket
        print(f'Downloading {bucket_path}')
        fz_fn = download_blob(bucket_path, destination=tmp_dir, bucket=bucket)

        # Unpack the FITS file
        print(f'Unpacking {fz_fn}')
        try:
            fits_fn = fits_utils.funpack(fz_fn)
            if not os.path.exists(fits_fn):
                raise FileNotFoundError(f"No {fits_fn} after unpacking")
        except Exception as e:
            update_state('error_unpacking', image_id=image_id)
            raise Exception(f'Problem unpacking {fz_fn}: {e!r}')

        # Check for existing WCS info
        print(f'Getting existing WCS for {fits_fn}')
        wcs_info = fits_utils.get_wcsinfo(fits_fn)
        already_solved = len(wcs_info) > 1

        print(f'WCS exists: {already_solved} {fits_fn}')

        try:
            background_subtracted = fits_utils.getval(fits_fn, 'BKGSUB')
        except KeyError:
            background_subtracted = False

        print(f'Background subtracted: {background_subtracted} {fits_fn}')
        # Do background subtraction
        if subtract_background and background_subtracted is False:
            fits_fn = pipeline.subtract_color_background(fits_fn, bucket_path)

        # Solve fits file
        if not already_solved or force:
            print(f'Plate-solving {fits_fn}')
            try:
                fits_utils.get_solve_field(fits_fn,
                                           skip_solved=False,
                                           overwrite=True,
                                           timeout=90,
                                           verbose=True)
                print(f'Solved {fits_fn}')
            except Exception as e:
                print(f'File not solved, skipping: {fits_fn} {e!r}')
                update_state('error_solving', image_id=image_id)
                return False
        else:
            print(f'Found existing WCS for {fz_fn}')

        # Pack file
        print(f'Uploading subtracted and solved fits file to {processed_bucket} {fz_fn}')
        fz_fn = fits_utils.fpack(fits_fn)
        # Upload new file to processed bucket
        upload_blob(fz_fn, bucket_path, bucket=processed_bucket)

        # Lookup point sources
        try:
            print(f'Looking up sources for {fits_fn}')
            point_sources = lookup_point_sources(
                fits_fn,
                max_catalog_separation=15,  # arcsec
                force_new=True,
                cursor=catalog_db_cursor
            )

            # Adjust some of the header items
            point_sources['bucket_path'] = bucket_path
            point_sources['image_id'] = image_id
            point_sources['seq_time'] = seq_time
            point_sources['img_time'] = img_time
            point_sources['unit_id'] = unit_id
            point_sources['camera_id'] = cam_id
            print(f'Sources detected: {len(point_sources)} {fz_fn}')
            update_state('sources_detected', image_id=image_id)
        except Exception as e:
            print(f'Error in detection: {fits_fn} {e!r}')
            update_state('error_sources_detection', image_id=image_id)
            raise e

        print(f'Extracting postage stamps for {fits_fn}')
        pipeline.get_postage_stamps(point_sources, fits_fn, tmp_dir=tmp_dir)
        update_state('sources_extracted', image_id=image_id)

        return True

    except Exception as e:
        print(f'Error while solving field: {e!r}')
        update_state('sources_extracted', image_id=image_id)
        return False
    finally:
        print(f'Solve and extraction complete, cleaning up for {bucket_path}')


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

    return destination


def update_state(state, sequence_id=None, image_id=None):
    """Update the state of the current image or sequence."""
    requests.post(update_state_url, json={'sequence_id': sequence_id,
                                          'image_id': image_id,
                                          'state': state
                                          })

    return True


def get_state(sequence_id=None, image_id=None):
    """Gets the state of the current image or sequence."""
    res = requests.post(get_state_url, json={'sequence_id': sequence_id,
                                             'image_id': image_id,
                                             })

    if res.ok:
        return res.json()['data']['state']

    return None


if __name__ == '__main__':
    main()
