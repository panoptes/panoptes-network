import os
import time

from google.cloud import logging
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub

import pandas as pd
from astropy import units as u
from astropy.time import Time

from pocs.utils.images import fits as fits_utils
from piaa.utils.postgres import get_cursor
from piaa.utils import pipeline

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
SUB_NAME = os.getenv('SUB_TOPIC', 'plate-solver-sub')

logging_client = logging.Client()
bq_client = bigquery.Client()
storage_client = storage.Client(project=PROJECT_ID)
subscriber_client = pubsub.SubscriberClient()

bucket = storage_client.get_bucket(BUCKET_NAME)

sub_name = f'projects/{PROJECT_ID}/subscriptions/{SUB_NAME}'

db_cursor = None

logging_client.setup_logging()

import logging


def main():
    logging.info(f"Starting pubsub listen on {sub_name}")

    try:
        future = subscriber_client.subscribe(sub_name, callback=msg_callback)

        # Keeps main thread from exiting.
        logging.info(f"Subscriber started, entering listen loop")
        while True:
            time.sleep(10)
    except Exception as e:
        logging.warn(f'Problem starting subscriber: {e!r}')
        future.cancel()


def msg_callback(message):
    attributes = message.attributes

    event_type = attributes['eventType']
    object_id = attributes['objectId']
    overwrote_generation = attributes['overwroteGeneration']

    new_file = overwrote_generation == ""

    logging.info(f'File: {object_id}')
    logging.info(f'Event Type: {event_type}')
    logging.info(f'New file?: {new_file}')

    if (event_type is 'OBJECT_FINALIZE' and new_file):
        # TODO: Add CR2 handling
        if object_id.endswith('.fz') or object_id.endswith('.fits'):
            logging.info(f'Solving {object_id}')
            status = solve_file(object_id)
            if status['status'] == 'sources_extracted':
                message.ack()
    else:
        # If an overwrite then simply ack message
        message.ack()


def solve_file(object_id):
    global db_cursor

    unit_id, field, cam_id, seq_time, file = object_id.split('/')
    sequence_id = f'{unit_id}_{cam_id}_{seq_time}'

    # Download file blob from bucket
    logging.info(f'Downloading {object_id}')
    fz_fn = download_blob(object_id, destination='/tmp', bucket=bucket)

    # Check for existing WCS info
    wcs_info = fits_utils.get_wcsinfo(fz_fn)

    # Unpack the FITS file
    fits_fn = fits_utils.fpack(fz_fn, unpack=True)

    # Solve fits file
    logging.info(f'Plate-solving {fits_fn}')
    solve_info = fits_utils.get_solve_field(fits_fn, timeout=90)

    if db_cursor is None:
        db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')

    # Lookup point sources
    logging.info(f'Looking up sources for {fits_fn}')
    point_sources = pipeline.lookup_point_sources(
        fits_fn,
        force_new=True,
        cursor=db_cursor
    )

    # Adjust some of the header items
    header = fits_utils.getheader(fits_fn)
    obstime = Time(pd.to_datetime(file.split('.')[0]))
    exptime = header['EXPTIME'] * u.second
    obstime += (exptime / 2)
    point_sources['obstime'] = obstime.datetime
    point_sources['exptime'] = exptime
    point_sources['airmass'] = header['AIRMASS']
    point_sources['file'] = file
    point_sources['sequence'] = sequence_id

    # Send to bigquery
    logging.info(f'Sending {len(point_sources)} sources to bigquery')
    dataset_ref = bq_client.dataset('observations')
    sources_table_ref = dataset_ref.table('sources')
    bq_client.load_table_from_dataframe(point_sources, sources_table_ref).result()

    # Upload solved file if newly solved (i.e. nothing besides filename in wcs_info)
    if solve_info is not None and len(wcs_info) == 1:
        fz_fn = fits_utils.fpack(fits_fn)
        upload_blob(fz_fn, object_id, bucket=bucket)

    return {'status': 'sources_extracted', 'filename': fits_fn, }


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

    logging.info('Blob {} downloaded to {}.'.format(
        source_blob_name,
        destination))

    return destination


def upload_blob(source_file_name, destination, bucket=None, bucket_name='panoptes-survey'):
    """Uploads a file to the bucket."""
    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    logging.info('File {} uploaded to {}.'.format(
        source_file_name,
        destination))


if __name__ == '__main__':
    main()
