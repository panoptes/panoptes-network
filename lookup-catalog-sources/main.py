import base64
import os
import sys
import tempfile

from astropy.wcs import WCS
from flask import Flask, request
from google.cloud import firestore
from google.cloud import storage
from panoptes.utils import sequence_id_from_path
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.logger import logger
from panoptes.utils.stars import get_stars_from_footprint

logger.enable('panoptes')

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-processed-observations')

raw_bucket = storage.Client().bucket(BUCKET_NAME)
firestore_db = firestore.Client()

app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        data = base64.b64decode(pubsub_message['data']).decode('utf-8').strip()

    attributes = pubsub_message['attributes']

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
                    in firestore_db.collection('images').where('sequence_id', '==', sequence_id).limit(1).stream()
                    ]
        bucket_path = url_list[0]

    if image_id is not None:
        logger.debug(f'Using image_id={image_id} to get bucket_path')
        bucket_path = firestore_db.document(f'images/{image_id}').get(['public_url']).get('public_url')

    process_topic(bucket_path)

    # Flush the stdout to avoid log buffering.
    sys.stdout.flush()

    return ('', 204)


def process_topic(bucket_path):
    sequence_id = sequence_id_from_path(bucket_path)
    logger.info(f'Received bucket_path={bucket_path} for catalog sources lookup')

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

    # Save catalog sources as output file.
    with tempfile.TemporaryDirectory() as tmp_dir:
        sources_bucket_path = f'{sequence_id}.{format}'
        local_path = os.path.join(tmp_dir, sources_bucket_path)
        logger.debug(f'Saving catalog sources to {sources_bucket_path}')

        output_func = getattr(catalog_sources, f'to_{format}')

        local_fn = output_func(local_path, index=False, compression='GZIP')

        raw_bucket.blob(sources_bucket_path).upload_from_filename(local_fn)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=True)
