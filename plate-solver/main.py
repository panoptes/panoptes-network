import os
import sys
import base64
import tempfile

from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import firestore
from google.cloud import storage

from astropy.io import fits
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.serializers import from_json
from panoptes.utils.bayer import get_rgb_background

try:
    db = firestore.Client()
except Exception as e:
    print(f'Error getting firestore client: {e!r}')

app = Flask(__name__)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')

# Storage
try:
    storage_client = storage.Client(project=PROJECT_ID)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')


@app.route('/', methods=['POST'])
def main():
    """ You shouldn't need to change anything here. """
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


def process_topic(data,):
    """Plate-solve a FITS file.

    Returns:
        TYPE: Description
    """
    bucket_name = data.get('bucket_name', BUCKET_NAME)
    bucket_path = data.get('bucket_path', None)
    solve_config = data.get('solve_config', {
        "skip_solved": False,
        "timeout": 120
    })
    background_config = data.get('background_config', {
        "force_new": True,
        "camera_bias": 2048.,
        "filter_size": 20,
    })
    print(f"Plate-solving FITS file {bucket_path}")
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

                image_id = fits_utils.getval(local_path, 'IMAGEID')
                status = db.document(f'images/{image_id}').get('status')
                if status == 'solved':
                    return jsonify(bucket_uri=fits_blob.public_url, status='solved')

                # Do the actual plate-solve.
                solved_path = solve_file(local_path, background_config, solve_config)

                # Replace file on bucket with solved file.
                print(f'Uploading {solved_path} to {fits_blob.public_url}')
                fits_blob.upload_from_filename(solved_path)

                # Update firestore record
                db.document(f'images/{image_id}').set(dict(status='solved'), merge=True)

                return jsonify(bucket_uri=fits_blob.public_url, status='solved')
            except Exception as e:
                print(f'Problem with plate solving file: {e!r}')
                db.document(f'images/{image_id}').set(dict(status='solve_error'), merge=True)
                return jsonify(error=e)
            finally:
                print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')


def solve_file(local_path, background_config, solve_config):
    print(f'Solving {local_path}')
    solved_file = None

    observation_background = get_rgb_background(local_path, **background_config)
    if observation_background is None:
        return None

    print(f'Plate solving for {local_path}')
    try:
        # Get the background subtracted data.
        header = fits_utils.getheader(local_path)
        data = fits_utils.getdata(local_path)
        # Save subtracted file locally.
        hdu = fits.PrimaryHDU(data=data - observation_background, header=header)

        back_path = local_path.replace('.fits', '-background.fits')
        hdu.writeto(back_path, overwrite=True)

        print(f'Plate solving {back_path} with args: {solve_config!r}')
        solve_info = fits_utils.get_solve_field(back_path, **solve_config)
        solved_file = solve_info['solved_fits_file'].replace('.new', '.fits')

        # Save over original file with new headers but old data.
        solved_header = fits_utils.getheader(solved_file)
        solved_header['status'] = 'solved'
        hdu = fits.PrimaryHDU(data=data, header=solved_header)
        hdu.writeto(local_path, overwrite=True)

    except Exception as e:
        print(f'Problem with plate solving: {e!r}')
    finally:
        return local_path


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
