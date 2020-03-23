import os
import sys
import base64
import tempfile
from warnings import warn

from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import storage

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.serializers import from_json


app = Flask(__name__)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')

# Storage
try:
    print(f'Loading google storage credentials')
    storage_client = storage.Client(project=PROJECT_ID)
except Exception as e:
    warn(f"Can't load Google credentials, exiting: {e!r}")
    # sys.exit(1)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')


@app.route('/', methods=['POST'])
def main():
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

    data = dict()
    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        data = from_json(base64.b64decode(pubsub_message['data']).decode('utf-8').strip())

    print(f'Received {data!r}')
    process_topic(data)

    # Flush the stdout to avoid log buffering.
    sys.stdout.flush()

    return ('', 204)


def process_topic(data):
    """Compress a FITS file.

    Returns:
        TYPE: Description
    """
    print(f"Compressing FITS file.")
    bucket_name = data.get('bucket_name', BUCKET_NAME)
    bucket_path = data.get('bucket_path', None)
    if bucket_path is not None:

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
            bucket = storage_client.get_bucket(bucket_name)
            try:
                print(f'Getting blob for {bucket_path}.')
                fits_blob = bucket.get_blob(bucket_path)
                if not fits_blob:
                    return jsonify(success=False, msg=f"Can't find {bucket_path} in {bucket_name}")

                # Download file
                print(f'Downloading image for {bucket_path}.')
                local_path = os.path.join(tmp_dir_name, bucket_path.replace('/', '-'))
                with open(local_path, 'wb') as f:
                    fits_blob.download_to_file(f)

                print(f'Compressing {local_path}')
                compressed_path = fits_utils.fpack(local_path)
                destination = compressed_path.replace(f'{tmp_dir_name}/', '').replace('-', '/')

                # Upload file to blob
                print(f'Uploading {compressed_path} to gs://{bucket_name}/{destination}')
                blob = storage_client.get_bucket(bucket_name).blob(destination)
                blob.upload_from_filename(compressed_path)

                # Remove original file
                print(f'Deleting {bucket_path}')
                fits_blob.delete()

                return jsonify(bucket_uri=blob.public_url)
            except Exception as e:
                print(f'Problem with compressing file: {e!r}')
                return jsonify(error=e)
            finally:
                print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
