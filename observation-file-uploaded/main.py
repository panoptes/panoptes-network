import base64
import json
import os
import sys

import pandas as pd
import pendulum
import requests
from google.cloud import bigquery

BASE_URL = os.getenv('BASE_URL', 'https://storage.googleapis.com/panoptes-observations/')
FITS_HEADER_URL = 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header'

bq_client = bigquery.Client()

SOURCE_COLUMNS = [
    'picid',
    'time',
    'sequence_id',
    'catalog_ra',
    'catalog_dec',
    'catalog_vmag',
    'catalog_vmag_err',
    'x',
    'y',
    'x_int',
    'y_int',
    'twomass',
    'gaia',
    'unit_id',
]
HEADER_COLUMNS = {
    'IMAGEID': 'image_id',
    'CRVAL1': 'image_ra_center',
    'CRVAL2': 'image_dec_center',
    'ISO': 'camera_iso',
    'CAMTEMP': 'camera_temp',
    'CIRCCONF': 'camera_circconf',
    'COLORTMP': 'camera_colortemp',
    'INTSN': 'camera_lens_serial_number',
    'CAMSN': 'camera_serial_number',
    'MEASEV': 'camera_measured_ev',
    'MEASEV2': 'camera_measured_ev2',
    'MEASRGGB': 'camera_measured_rggb',
    'WHTLVLN': 'camera_white_lvln',
    'WHTLVLS': 'camera_white_lvls',
    'REDBAL': 'camera_red_balance',
    'BLUEBAL': 'camera_blue_balance',
    'LAT-OBS': 'site_latitude',
    'LONG-OBS': 'site_longitude',
    'ELEV-OBS': 'site_elevation',
}
METADATA_COLUMNS = {
    'unit_id': 'unit_id',
    'sequence_id': 'sequence_id',
    'image_id': 'image_id',
    'time': 'time',
    'ra_mnt': 'mount_ra',
    'ha_mnt': 'mount_ha',
    'dec_mnt': 'mount_dec',
    'ra_image': 'image_ra',
    'dec_image': 'image_dc',
    'airmass': 'image_airmass',
    'moonsep': 'image_moonsep',
    'moonfrac': 'image_moonfrac',
    'exptime': 'image_exptime',
    'camera_iso': 'camera_iso',
    'camera_temp': 'camera_temp',
    'camera_circconf': 'camera_circconf',
    'camera_colortemp': 'camera_colortemp',
    'camera_lens_serial_number': 'camera_lens_serial_number',
    'camera_serial_number': 'camera_serial_number',
    'camera_measured_ev': 'camera_measured_ev',
    'camera_measured_ev2': 'camera_measured_ev2',
    'camera_measured_rggb': 'camera_measured_rggb',
    'camera_white_lvln': 'camera_white_lvln',
    'camera_white_lvls': 'camera_white_lvls',
    'camera_red_balance': 'camera_red_balance',
    'camera_blue_balance': 'camera_blue_balance',
    'site_latitude': 'site_latitude',
    'site_longitude': 'site_longitude',
    'site_elevation': 'site_elevation',
    'bucket_path': 'bucket_path',
    'public_url': 'public_url',
}


def entry_point(raw_message, context):
    """Background Cloud Function to be triggered by Cloud Storage.

    This will send a pubsub message to a certain topic depending on
    what type of file was uploaded. The servies responsible for those
    topis do all the processing.

    Args:
        message (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    try:
        message = json.loads(base64.b64decode(raw_message['data']).decode('utf-8'))
        attributes = raw_message['attributes']
        print(f"Message: {message!r} \t Attributes: {attributes!r}")

        process_topic(message, attributes)
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()

    except Exception as e:
        print(f'Error: {e}')


def process_topic(message, attributes):
    """Look for uploaded files and process according to the file type.

    Args:
        message (dict): The Cloud Functions event payload.
        attributes (dict): The message attributes.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    bucket_path = attributes['objectId']
    bucket_link = message['mediaLink']

    if 'overwroteGeneration' in attributes:
        print(f'File already exists in bucket, skipping import for {bucket_link}')
        return

    if bucket_path is None:
        raise Exception(f'No file requested')

    print(f'Looking up {bucket_link}')
    try:
        df = pd.read_csv(bucket_link)
    except Exception as e:
        print(f'Error with lookup: {e!r}')
        return

    bq_table = None
    sequence_id = bucket_path.split('/')[-1].split('-')[0]
    print(f'Found sequence_id={sequence_id}')

    if 'sources' in bucket_path:
        # TODO make sequence_id_from_path work here.
        unit_id, camera_id, observation_time = sequence_id.split('_')
        df['unit_id'] = unit_id
        df['sequence_id'] = sequence_id
        df['camera_id'] = camera_id
        df['time'] = pendulum.parse(observation_time)

        df = df[SOURCE_COLUMNS]
        bq_table = 'sources'

    if 'metadata' in bucket_path:
        # Look up fits headers
        fits_list = df.public_url.tolist()
        print(f'Looking up headers for {len(fits_list)}')
        headers = [get_header(f) for f in fits_list]
        headers = [h for h in headers if type(h) == dict]

        # Build DataFrame.
        print(f'Making DataFrame for headers')
        headers_df = pd.DataFrame(headers)[list(HEADER_COLUMNS.keys())].convert_dtypes().dropna()

        # Clean values.
        headers_df['MEASRGGB'] = headers_df.MEASRGGB.map(lambda x: x.split(' '))
        headers_df['CAMTEMP'] = headers_df.CAMTEMP.map(lambda x: x.split(' ')[0])
        headers_df['CIRCCONF'] = headers_df.CIRCCONF.map(lambda x: x.split(' ')[0])

        # Give better column names.
        headers_df = headers_df.convert_dtypes().rename(columns=HEADER_COLUMNS)

        print(f'Merging headers DataFrame with metadata')
        df = df.merge(headers_df, on='image_id')

        # Rename to friendlier columns.
        df = df[list(METADATA_COLUMNS.keys())].rename(columns=METADATA_COLUMNS).convert_dtypes()

        bq_table = 'metadata'

    if not bq_table:
        print(f'No table given in {bucket_path}')

    df['insert_time'] = pendulum.now()
    print(f'Sending {len(df)} rows to observations.{bq_table}')
    job_config = bigquery.LoadJobConfig(schema=[
        bigquery.SchemaField("time", "TIMESTAMP"),
        bigquery.SchemaField("insert_time", "TIMESTAMP"),
    ])

    job = bq_client.load_table_from_dataframe(
        df.convert_dtypes(),
        f'observations.{bq_table}',
        job_config=job_config
    )

    # Wait for the load job to complete.
    job.result()


def get_header(bucket_path):
    """Small helper function to lookup FITS header"""
    res = requests.post(FITS_HEADER_URL, json=dict(bucket_path=bucket_path))
    try:
        h0 = res.json()['header']
    except Exception:
        h0 = dict()

    return h0
