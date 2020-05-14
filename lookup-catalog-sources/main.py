import os
import sys
from io import BytesIO

import numpy as np
import pandas as pd
import pendulum
import requests
from astropy.utils.data import clear_download_cache
from google.cloud import bigquery
from google.cloud import firestore
from google.cloud import pubsub
from google.cloud import pubsub_v1
from google.cloud import storage
from panoptes.utils import image_id_from_path
from panoptes.utils import sequence_id_from_path
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.logger import logger
from panoptes.utils.stars import get_stars_from_footprint

logger.enable('panoptes')

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-observations')

PUBSUB_SUBSCRIPTION = 'read-lookup-catalog-sources'
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 1)

FITS_HEADER_URL = 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header'

SOURCE_COLUMNS = [
    'picid',
    'time',
    'sequence_id',
    'catalog_ra',
    'catalog_dec',
    'catalog_vmag',
    'catalog_vmag_err',
    'catalog_vmag_bin',
    'x',
    'y',
    'x_int',
    'y_int',
    'twomass',
    'gaia',
    'unit_id',
]

METADATA_COLUMNS = {
    'unit_id': 'unit_id',
    'sequence_id': 'sequence_id',
    'image_id': 'image_id',
    'time': 'time',
    'ra_mnt': 'mount_ra',
    'ha_mnt': 'mount_ha',
    'dec_mnt': 'mount_dec',
    'ra_image': 'image_ra',
    'dec_image': 'image_dec',
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
    'camera_measured_r': 'camera_measured_r',
    'camera_measured_g1': 'camera_measured_g1',
    'camera_measured_g2': 'camera_measured_g2',
    'camera_measured_b': 'camera_measured_b',
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

# Storage
try:
    bq_client = bigquery.Client()
    firestore_db = firestore.Client()
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, PUBSUB_SUBSCRIPTION)

    storage_client = storage.Client()
    output_bucket = storage.Client().bucket(BUCKET_NAME)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


def main():
    print(f'Creating subscriber (messages={MAX_MESSAGES}) for {subscription_path}')
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=process_topic,
        flow_control=pubsub_v1.types.FlowControl(max_messages=int(MAX_MESSAGES))
    )

    print(f'Listening for messages on {subscription_path}')
    with subscriber:
        try:
            streaming_pull_future.result()  # Blocks indefinitely
        except Exception as e:
            streaming_pull_future.cancel()
            print(f'Streaming pull cancelled: {e!r}')
        finally:
            print(f'Streaming pull finished')


def process_topic(message):
    data = message.data.decode('utf-8')
    attributes = dict(message.attributes)

    sequence_id = attributes.get('sequence_id')
    image_id = attributes.get('image_id')
    bucket_path = attributes.get('bucket_path')

    # Options
    force = attributes.get('force', False)

    # Get a document for the observation and the image. If only given a
    # sequence_id, then look up a solved image.
    if sequence_id is not None:
        logger.debug(f'Using sequence_id={sequence_id} to get bucket_path')
        url_list = [d.get('public_url')
                    for d
                    in firestore_db.collection('images')
                        .where('sequence_id', '==', sequence_id)
                        .where('status', '==', 'solved')
                        .limit(1)
                        .stream()
                    ]
        try:
            bucket_path = url_list[0]
        except IndexError:
            logger.info(f'No solved images found for {sequence_id}')
            message.ack()
            return

    if image_id is not None:
        logger.debug(f'Using image_id={image_id} to get bucket_path')
        bucket_path = firestore_db.document(f'images/{image_id}').get(['public_url']).get('public_url')

    image_id = image_id_from_path(bucket_path)
    sequence_id = sequence_id_from_path(bucket_path)
    logger.info(f'Received bucket_path={bucket_path} for catalog sources lookup')

    observation_doc_ref = firestore_db.document(f'observations/{sequence_id}')
    obs_status = observation_doc_ref.get(['status']).get('status')

    if obs_status != 'receiving_files' and not force:
        logger.warning(f'Observation status={obs_status}. Will only proceed if stats=received_files or force=True')
        message.ack()
        return

    # If given a relative path instead of url, attempt default public location.
    if not bucket_path.startswith('https'):
        bucket_path = f'https://storage.googleapis.com/panoptes-raw-images/{bucket_path}'
        logger.debug(f'Given bucket_path looks like a relative path, change to url={bucket_path}')

    wcs = fits_utils.getwcs(bucket_path)
    if not wcs.is_celestial:
        logger.warning(f'Image says it is plate-solved but WCS is not valid.')
        firestore_db.document(f'images/{image_id}').set(dict(status='needs-solve', solved=False), merge=True)
        # Force the message to re-send where it will hopefully pick up a correctly solved image.
        message.nack()

        # Clear the download cache.
        logger.debug(f'Clearing download cache for {bucket_path}')
        clear_download_cache(bucket_path)
        return

    logger.debug(f'Looking up sources for {sequence_id} {wcs}')
    catalog_sources = get_stars_from_footprint(wcs, bq_client=bq_client)
    logger.debug(f'Found {len(catalog_sources)} sources in {sequence_id}')

    # Get the XY positions via the WCS
    logger.debug(f'Getting XY positions for {sequence_id}')
    catalog_coords = catalog_sources[['catalog_ra', 'catalog_dec']]
    catalog_xy = wcs.all_world2pix(catalog_coords, 1)
    catalog_sources['x'] = catalog_xy.T[0]
    catalog_sources['y'] = catalog_xy.T[1]
    catalog_sources['x_int'] = catalog_sources.x.astype(int)
    catalog_sources['y_int'] = catalog_sources.y.astype(int)

    # Get additional metadata.
    unit_id, camera_id, observation_time = sequence_id.split('_')
    catalog_sources['unit_id'] = unit_id
    catalog_sources['sequence_id'] = sequence_id
    catalog_sources['camera_id'] = camera_id
    catalog_sources['time'] = pendulum.parse(observation_time).replace(tzinfo=None)
    catalog_sources['catalog_vmag_bin'] = catalog_sources['catalog_vmag'].apply(np.floor).astype('int')

    # Get just the columns we want.
    catalog_sources = catalog_sources[SOURCE_COLUMNS]

    sources_bucket_path = f'{sequence_id}-sources.parquet'
    logger.debug(f'Saving catalog sources to {sources_bucket_path}')

    # Lookup output format and save.
    bio = BytesIO()
    catalog_sources.convert_dtypes().dropna().to_parquet(bio, index=False)
    bio.seek(0)

    # Upload
    obs_blob = output_bucket.blob(sources_bucket_path)
    obs_blob.upload_from_file(bio)
    logger.debug(f'Observation metadata saved to {obs_blob.public_url}')

    # Update observation status
    wcs_ra = wcs.wcs.crval[0]
    wcs_dec = wcs.wcs.crval[1]
    logger.debug(f'Updating observation status and coordinates for {sequence_id}')
    observation_doc_ref.set(dict(status='solved', ra=wcs_ra, dec=wcs_dec), merge=True)

    # Update observation metadata file
    update_observation_file(sequence_id)

    # Clear the WCS from the cache.
    logger.debug(f'Clearing download cache for {bucket_path}')
    clear_download_cache(bucket_path)

    logger.debug(f'Acking message for {bucket_path}')
    message.ack()


def update_observation_file(sequence_id):
    print(f'Updating {sequence_id} static file')

    # Build query
    obs_query = firestore_db.collection('images').where('sequence_id', '==', sequence_id)

    # Fetch documents into a DataFrame.
    metadata_df = pd.DataFrame([dict(image_id=doc.id, **doc.to_dict()) for doc in obs_query.stream()])
    print(f'{sequence_id}: Caching {len(metadata_df)} results from lookup')

    # Look up fits headers
    fits_list = metadata_df.public_url.tolist()
    print(f'Looking up headers for {len(fits_list)}')
    headers = [get_header(f) for f in fits_list]
    headers = [h for h in headers if type(h) == dict]

    # Build DataFrame.
    print(f'Making DataFrame for headers')
    headers_df = pd.DataFrame(headers)[list(HEADER_COLUMNS.keys())].convert_dtypes().dropna()

    # Clean values.
    rggb_df = headers_df['MEASRGGB'].str.split(' ', expand=True).rename(columns={
        0: 'camera_measured_r',
        1: 'camera_measured_g1',
        2: 'camera_measured_g2',
        3: 'camera_measured_b',
    }).astype('int')
    headers_df = headers_df.join(rggb_df)
    headers_df['CAMTEMP'] = headers_df.CAMTEMP.map(lambda x: float(x.split(' ')[0]))
    headers_df['CIRCCONF'] = headers_df.CIRCCONF.map(lambda x: float(x.split(' ')[0]))

    # Give better column names.
    headers_df = headers_df.convert_dtypes(convert_integer=False).rename(columns=HEADER_COLUMNS)

    print(f'Merging headers DataFrame with metadata')
    metadata_df = metadata_df.merge(headers_df, on='image_id')

    # Rename to friendlier columns.
    metadata_df = metadata_df[list(METADATA_COLUMNS.keys())].rename(columns=METADATA_COLUMNS).convert_dtypes()

    # Force dtypes on certain columns.
    metadata_df['site_elevation'] = metadata_df['site_elevation'].astype('float')
    metadata_df['image_exptime'] = metadata_df['image_exptime'].astype('float')
    metadata_df['camera_temp'] = metadata_df['camera_temp'].astype('float')
    metadata_df['camera_colortemp'] = metadata_df['camera_colortemp'].astype('int')
    metadata_df['camera_lens_serial_number'] = metadata_df['camera_lens_serial_number'].astype('string')
    metadata_df['camera_serial_number'] = metadata_df['camera_serial_number'].astype('string')

    bio = BytesIO()
    metadata_df.dropna().to_parquet(bio, index=False)
    bio.seek(0)

    # Upload file object to public blob.
    blob = output_bucket.blob(f'{sequence_id}-metadata.parquet')
    blob.upload_from_file(bio)
    print(f'Observations file available at: {blob.public_url}')


def get_header(bucket_path):
    """Small helper function to lookup FITS header"""
    res = requests.post(FITS_HEADER_URL, json=dict(bucket_path=bucket_path))
    try:
        h0 = res.json()['header']
    except Exception:
        h0 = dict()

    return h0


if __name__ == '__main__':
    main()
