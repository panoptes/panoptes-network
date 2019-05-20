#!/usr/bin/env python

import os
import sys
import time
from contextlib import suppress

from google.cloud import storage
from google.cloud import pubsub

from dateutil.parser import parse as parse_date
from astropy.io import fits

import csv
import requests

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.google.cloudsql import get_cursor
from panoptes.utils import bayer
from panoptes.piaa.utils import pipeline

if ((os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '') == '') and
        (os.environ.get('GOOGLE_COMPUTE_INSTANCE', '') == '')):
    print(f"Don't know how to authenticate, refusing to run.")
    sys.exit(1)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'gce-plate-solver')
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


def main():
    print(f"Starting pubsub listen on {pubsub_sub_path}")

    try:
        # max_messages means we only process one at a time.
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            pubsub_sub_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        print(f"Plate-solver subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        print(f'Problem in message callback: {e!r}')
        future.cancel()


def msg_callback(message):

    attributes = message.attributes
    bucket_path = attributes['bucket_path']
    object_id = attributes['object_id']
    force = attributes.get('force', False)

    if force:
        print(f'Found force=True, forcing new plate solving')

    try:
        # Get DB cursors
        catalog_db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')
        metadata_db_cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

        print(f'Solving {bucket_path}')
        solve_file(bucket_path,
                   object_id,
                   catalog_db_cursor,
                   metadata_db_cursor,
                   force=force)
        print(f'Finished processing {bucket_path}.')
    except Exception as e:
        raise Exception(f'Problem with solve file: {e!r}')
    finally:
        catalog_db_cursor.close()
        metadata_db_cursor.close()
        # Acknowledge message
        message.ack()


def solve_file(bucket_path, object_id, catalog_db_cursor, metadata_db_cursor, force=False):

    try:  # Wrap everything so we can do file cleanup

        unit_id, field, cam_id, seq_time, file = bucket_path.split('/')
        img_time = file.split('.')[0]
        image_id = f'{unit_id}_{cam_id}_{img_time}'

        # Don't process pointing images.
        if 'pointing' in bucket_path:
            print(f'Skipping pointing file.')
            update_state('skipped', image_id=image_id)
            return

        # Don't process files that have been processed.
        if (force is False) and (get_state(image_id=image_id) == 'sources_extracted'):
            print(f'Skipping already processed image.')
            return

        # Download file blob from bucket
        print(f'Downloading {bucket_path}')
        fz_fn = download_blob(bucket_path, destination='/tmp', bucket=bucket)

        # Unpack the FITS file
        print(f'Unpacking {fz_fn}')
        fits_fn = fits_utils.fpack(fz_fn, unpack=True)
        if not os.path.exists(fits_fn):
            update_state('error_unpacking', image_id=image_id)
            raise Exception(f'Problem unpacking {fz_fn}')

        # Check for existing WCS info
        print(f'Getting existing WCS for {fits_fn}')
        wcs_info = fits_utils.get_wcsinfo(fits_fn)
        already_solved = len(wcs_info) > 1

        if not already_solved or force:
            # Solve fits file
            print(f'Plate-solving {fits_fn}')
            try:
                solve_info = fits_utils.get_solve_field(fits_fn,
                                                        skip_solved=False,
                                                        overwrite=True,
                                                        timeout=90)
                print(f'Solved {fits_fn}')
            except Exception as e:
                print(f'File not solved, skipping: {fits_fn} {e!r}')
                update_state('error_solving', image_id=image_id)
                return None
        else:
            print(f'Found existing WCS for {fz_fn}')
            solve_info = None

        # Lookup point sources
        try:
            print(f'Looking up sources for {fits_fn}')
            point_sources = pipeline.lookup_point_sources(
                fits_fn,
                force_new=True,
                cursor=catalog_db_cursor
            )

            # Adjust some of the header items
            point_sources['gcs_file'] = object_id
            point_sources['image_id'] = image_id
            point_sources['seq_time'] = seq_time
            point_sources['img_time'] = img_time
            point_sources['unit_id'] = unit_id
            point_sources['camera_id'] = cam_id
            print(f'Sources detected: {len(point_sources)} {fz_fn}')
            update_state('sources_detected', image_id=image_id)
        except Exception as e:
            update_state('error_sources_detection', image_id=image_id)
            raise e

        print(f'Looking up sources for {fits_fn}')
        get_sources(point_sources, fits_fn)
        update_state('sources_extracted', image_id=image_id)

        # Upload solved file if newly solved (i.e. nothing besides filename in wcs_info)
        if solve_info is not None and (force is True or len(wcs_info) == 1):
            fz_fn = fits_utils.fpack(fits_fn)
            upload_blob(fz_fn, bucket_path, bucket=bucket)

        return

    except Exception as e:
        print(f'Error while solving field: {e!r}')
        return False
    finally:
        print(f'Solve and extraction complete, cleaning up for {bucket_path}')
        # Remove files
        for fn in [fits_fn, fz_fn]:
            with suppress(FileNotFoundError):
                os.remove(fn)

    return None


def get_sources(point_sources, fits_fn, stamp_size=10):
    """Get postage stamps for each PICID in the given file.

    Args:
        point_sources (`pandas.DataFrame`): A DataFrame containing the results from `sextractor`.
        fits_fn (str): The name of the FITS file to extract stamps from.
        stamp_size (int, optional): The size of the stamp to extract, default 10 pixels.
    """
    data = fits.getdata(fits_fn)
    image_id = None

    print(f'Extracting {len(point_sources)} point sources from {fits_fn}')

    row = point_sources.iloc[0]
    sources_csv_fn = f'{row.unit_id}-{row.camera_id}-{row.seq_time}-{row.img_time}.csv'
    print(f'Sources metadata will be extracted to {sources_csv_fn}')

    print(f'Starting source extraction for {fits_fn}')
    with open(sources_csv_fn, 'w') as metadata_fn:
        writer = csv.writer(metadata_fn, quoting=csv.QUOTE_MINIMAL)

        # Write out headers.
        csv_headers = [
            'picid',
            'unit_id',
            'camera_id',
            'sequence_time',
            'image_time',
            'x', 'y',
            'ra', 'dec',
            'sextractor_flags',
            'sextractor_background',
            'slice_y',
            'slice_x',
        ]
        csv_headers.extend([f'pixel_{i:02d}' for i in range(stamp_size**2)])
        writer.writerow(csv_headers)

        for picid, row in point_sources.iterrows():
            # Get the stamp for the target
            target_slice = bayer.get_stamp_slice(
                row.x, row.y,
                stamp_size=(stamp_size, stamp_size),
                ignore_superpixel=False,
                verbose=False
            )

            # Add the target slice to metadata to preserve original location.
            row['target_slice'] = target_slice
            stamp = data[target_slice].flatten().tolist()

            row_values = [
                int(picid),
                str(row.unit_id),
                str(row.camera_id),
                parse_date(row.seq_time),
                parse_date(row.img_time),
                int(row.x), int(row.y),
                row.ra, row.dec,
                int(row['flags']),
                row.background,
                target_slice[0],
                target_slice[1],
                *stamp
            ]

            # Write out stamp data
            writer.writerow(row_values)

    # Upload the CSV files.
    try:
        upload_blob(sources_csv_fn,
                    destination=sources_csv_fn.replace('-', '/'),
                    bucket_name='panoptes-detected-sources')
    except Exception as e:
        print(f'Uploading of sources failed for {sources_csv_fn}')
        update_state('error_uploading_sources', image_id=image_id)
    finally:
        # Remove generated files from local server.
        with suppress(FileNotFoundError):
            print(f'Cleaning up {sources_csv_fn}')
            os.remove(sources_csv_fn)

    return True


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
