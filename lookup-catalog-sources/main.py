import base64
import json
import os
import sys
import tempfile

import panoptes.utils.
from astropy.wcs import WCS
from google.cloud import storage
from panoptes.utils import sequence_id_from_path
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.logger import logger

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-processed-observations')

logger.enable('panoptes')

storage_client = storage.Client()
raw_bucket = storage_client.bucket(BUCKET_NAME)


def entry_point(pubsub_message, context):
    """Receive and process main request for topic.

    The arriving `pubsub_message` will be in a `PubSubMessage` format:

    https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage

    ```
        pubsub_message = {
          "data": string,
          "attributes": {
            string: string,
            ...
        }
        context = {
          "messageId": string,
          "publishTime": string
        }
    ```

    Args:
         pubsub_message (dict):  The dictionary with data specific to this type of
            pubsub_message. The `data` field contains the PubsubMessage message. The
            `attributes` field will contain custom attributes if there are any.
        context (google.cloud.functions.Context): The Cloud Functions pubsub_message
            metadata. The `event_id` field contains the Pub/Sub message ID. The
            `timestamp` field contains the publish time.
    """
    print(f'Function triggered with: {pubsub_message!r} {context!r}')

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        try:
            raw_string = base64.b64decode(pubsub_message['data']).decode()
            print(f'Raw message received: {raw_string!r}')
            data = json.loads(raw_string)

        except Exception as e:
            msg = ('Invalid Pub/Sub message: '
                   'data property is not valid base64 encoded JSON')
            print(f'{msg}: {e}')
            return f'Bad Request: {msg}', 400

        attributes = pubsub_message.get('attributes', dict())

        try:
            print(f'Processing: data={data!r} attributes={attributes!r}')
            process_topic(data, attributes)
            # Flush the stdout to avoid log buffering.
            sys.stdout.flush()
            return ('', 204)  # 204 is no-content success

        except Exception as e:
            print(f'error: {e}')
            return ('', 500)

    return ('', 500)


def process_topic(data, attributes=None):
    bucket_path = attributes.get('bucket_path')
    sequence_id = sequence_id_from_path(bucket_path)
    logger.info(f'Received {bucket_path} for catalog sources lookup, sequence_id={sequence_id}')

    # If given a relative path instead of url, attempt default public location.
    if not bucket_path.startswith('https'):
        bucket_path = f'https://storage.googleapis.com/panoptes-raw-images/{bucket_path}'
        logger.debug(f'Given bucket_path looks like a relative path, change to url={bucket_path}')

    headers = fits_utils.getheader(bucket_path)
    wcs = WCS(headers)

    logger.debug(f'Looking up sources for {sequence_id} {wcs}')
    catalog_sources = get_stars_from_footprint(wcs)
    logger.debug(f'Found {len(catalog_sources)} sources in {sequence_id}')

    # Get the XY positions via the WCS
    logger.debug(f'Getting XY positions for {sequence_id}')
    catalog_coords = catalog_sources[['catalog_ra', 'catalog_dec']]
    catalog_xy = wcs.all_world2pix(catalog_coords, 1)
    catalog_sources['x'] = catalog_xy.T[0]
    catalog_sources['y'] = catalog_xy.T[1]
    catalog_sources['x_int'] = catalog_sources.x.astype(int)
    catalog_sources['y_int'] = catalog_sources.y.astype(int)

    # Save catalog sources as parquet file.
    with tempfile.TemporaryDirectory() as tmp_dir:
        sources_bucket_path = f'{sequence_id}.parq'
        local_path = os.path.join(tmp_dir, sources_bucket_path)
        logger.debug(f'Saving catalog sources to {sources_bucket_path}')
        local_fn = catalog_sources.to_parquet(local_path, index=False, compression='GZIP')

        raw_bucket.blob(sources_bucket_path).upload_from_filename(local_fn)
