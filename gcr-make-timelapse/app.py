import os
import sys
import tempfile

from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import storage
import google.cloud.logging

from panoptes.utils.images import make_timelapse

import logging

app = Flask(__name__)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

# Storage
try:
    storage_client = storage.Client(project=PROJECT_ID)
except RuntimeError:
    logging.info(f"Can't load Google credentials, exiting")
    sys.exit(1)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')
LEGACY_BUCKET_NAME = os.getenv('LEGACY_BUCKET_NAME', 'panoptes-survey')

TIMELAPSE_BUCKET_NAME = os.getenv('PROCESSED_BUCKET_NAME', 'panoptes-timelapse')


@app.route('/', methods=['GET', 'POST'])
def main():
    """Get the latest records as JSON.

    Returns:
        TYPE: Description
    """
    logging.info(f"Making a new timelapse")
    if request.json:
        params = request.get_json(force=True)
        bucket_path = params.get('bucket_path', None)
        use_legacy = params.get('legacy', False)

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            logging.info(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
            try:
                logging.info(f'Downloading images for {bucket_path}.')
                download_blobs(bucket_path, tmp_dir_name, use_legacy=use_legacy)
                logging.info(f'Making timelapse for {bucket_path}.')
                # Save with underscores so it's one file, not in folders
                timelapse_fn = make_timelapse(tmp_dir_name,
                                              glob_pattern='PAN*20[1-9][0-9]*T[0-9]*.jpg',
                                              verbose=True)
                if timelapse_fn is None:
                    raise FileNotFoundError(f'Timelapse not created at {timelapse_fn}')
                logging.info(f'Uploading timelapse to {TIMELAPSE_BUCKET_NAME}: {timelapse_fn}.')

                # Upload with folder structure
                if use_legacy:
                    print(f'Found legacy path, removing field name')
                    unit_id, field_name, cam_id, seq_id = bucket_path.split('/')
                    bucket_path = os.path.join(unit_id, cam_id, seq_id)
                    print(f'New name: {bucket_path}')

                if bucket_path.endswith('/'):
                    bucket_path = bucket_path[:-1]

                timelapse_uri = upload_blob(timelapse_fn, f'{bucket_path}.mp4')
                return jsonify(timelapse_uri=timelapse_uri)
            except Exception as e:
                logging.info(f'Problem with timelapse: {e!r}')
                return jsonify(error=e)
            finally:
                logging.info(f'Cleaning up temporary directory: {tmp_dir_name} for {bucket_path}')
    else:
        return jsonify(error="No 'bucket_path' parameter given")


def download_blobs(bucket_path, dir_name, use_legacy=False):
    """Downloads a blob from the bucket."""
    if use_legacy:
        bucket = LEGACY_BUCKET_NAME
    else:
        bucket = BUCKET_NAME

    blobs = storage_client.list_blobs(bucket, prefix=bucket_path)

    # Get just the jpg images
    images = [b for b in blobs if b.name.endswith('jpg') and not b.name.startswith('pointing')]
    logging.info(f'Found {len(images)} images for {bucket_path}')

    image_names = list()
    for image in images:
        image_name = os.path.join(dir_name, image.name.replace('/', '_'))
        image.download_to_filename(image_name)
        image_names.append(image_name)


def upload_blob(source_file_name, destination):
    """Uploads a file to the bucket."""
    logging.info('Uploading {} to {}.'.format(source_file_name, destination))

    bucket = storage_client.get_bucket(TIMELAPSE_BUCKET_NAME)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    logging.info('File {} uploaded to {}.'.format(source_file_name, destination))

    return destination


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
