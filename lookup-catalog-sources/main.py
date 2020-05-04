import os
import sys
import tempfile

from google.cloud import bigquery
from google.cloud import firestore
from google.cloud import pubsub
from google.cloud import pubsub_v1
from google.cloud import storage
from panoptes.utils import sequence_id_from_path
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.logger import logger
from panoptes.utils.stars import get_stars_from_footprint

logger.enable('panoptes')

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-processed-observations')

PUBSUB_SUBSCRIPTION = 'read-lookup-catalog-sources'
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 1)

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
    format = attributes.get('format', 'parquet')
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
        bucket_path = url_list[0]

    if image_id is not None:
        logger.debug(f'Using image_id={image_id} to get bucket_path')
        bucket_path = firestore_db.document(f'images/{image_id}').get(['public_url']).get('public_url')

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

    # Save catalog sources as output file.
    with tempfile.TemporaryDirectory() as tmp_dir:
        sources_bucket_path = f'{sequence_id}.{format}'
        local_path = os.path.join(tmp_dir, sources_bucket_path)
        logger.debug(f'Saving catalog sources to {sources_bucket_path}')

        # Lookup output format and save.
        output_func = getattr(catalog_sources, f'to_{format}')
        output_func(local_path, index=False, compression='GZIP')

        # Upload
        output_bucket.blob(sources_bucket_path).upload_from_filename(local_path)

    # Update observation status
    wcs_ra = wcs.wcs.crval[0]
    wcs_dec = wcs.wcs.crval[1]
    logger.debug(f'Updating observation status and coordinates for {sequence_id}')
    observation_doc_ref.set(dict(status='solved', ra=wcs_ra, dec=wcs_dec), merge=True)

    message.ack()


if __name__ == '__main__':
    main()
