import os
from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import bigquery

import pandas as pd
from astropy import units as u
from astropy.time import Time

from pocs.utils.images import fits as fits_utils
from piaa.utils.postgres import get_cursor
from piaa.utils import pipeline
import storage

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
bq_client = bigquery.Client()
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')

app = Flask(__name__)


@app.route('/solve', methods=['POST'])
def solve_file():
    content = request.json
    bucket_fits_fn = content.get('filename', None)

    dataset_ref = bq_client.dataset('observations')
    sources_table_ref = dataset_ref.table('sources')

    unit_id, field, cam_id, seq_time, file = bucket_fits_fn.split('/')
    sequence_id = f'{unit_id}_{cam_id}_{seq_time}'

    # Download file blob from bucket
    fz_fn = storage.download_blob(bucket_fits_fn, destination='/tmp', bucket=bucket)

    # Unpack the FITS file
    fits_fn = fits_utils.fpack(fz_fn, unpack=True)

    # Solve fits file
    solve_info = fits_utils.get_solve_field(fits_fn, timeout=90)

    # Lookup point sources
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
    bq_client.load_table_from_dataframe(point_sources, sources_table_ref).result()

    # Upload solved file
    if solve_info is not None:
        fz_fn = fits_utils.fpack(fits_fn)
        storage.upload_blob(fz_fn, bucket_fits_fn, bucket=bucket)

    # Send the response
    return jsonify({'status': 'sources_extracted', 'file': fits_fn, }), 201


app.run(host='0.0.0.0', port=8080)
