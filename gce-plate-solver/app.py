import os
from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import storage
from google.cloud import bigquery
import google.cloud.logging

import pandas as pd
from astropy import units as u
from astropy.time import Time

from pocs.utils.images import fits as fits_utils
from piaa.utils.postgres import get_cursor
from piaa.utils import pipeline

# Instantiates a client
logging_client = google.cloud.logging.Client()

# Connects the logger to the root logging handler; by default this captures
# all logs at INFO level and higher
logging_client.setup_logging()

import logging

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
bq_client = bigquery.Client()
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

app = Flask(__name__)

db_cursor = None


@app.route('/echo', methods=['POST'])
def echo():
    content = request.json
    echo = content.get('echo', None)
    return jsonify({'echo': echo}), 201


@app.route('/solve', methods=['POST'])
def solve_file():
    global db_cursor

    content = request.json
    bucket_fits_fn = content.get('filename', None)

    dataset_ref = bq_client.dataset('observations')
    sources_table_ref = dataset_ref.table('sources')

    unit_id, field, cam_id, seq_time, file = bucket_fits_fn.split('/')
    sequence_id = f'{unit_id}_{cam_id}_{seq_time}'

    # Download file blob from bucket
    logging.info(f'Downloading {bucket_fits_fn}')
    fz_fn = download_blob(bucket_fits_fn, destination='/tmp', bucket=bucket)

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
    bq_client.load_table_from_dataframe(point_sources, sources_table_ref).result()

    # Upload solved file
    if solve_info is not None:
        fz_fn = fits_utils.fpack(fits_fn)
        upload_blob(fz_fn, bucket_fits_fn, bucket=bucket)

    # Send the response
    return jsonify({'status': 'sources_extracted', 'file': fits_fn, }), 201


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


app.run(host='0.0.0.0', port=8000)
