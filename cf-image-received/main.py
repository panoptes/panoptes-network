import os
import sys
import base64
import json
from flask import Flask
from flask import request
from contextlib import suppress

import requests

app = Flask(__name__)

add_header_endpoint = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-exp.cloudfunctions.net/record-image'
)

fits_packer_endpoint = os.getenv(
    'FPACK_ENDPOINT',
    'https://fits-packer-cezgvr32ga-uc.a.run.app/'
)

make_rgb_endpoint = os.getenv(
    'RGB_ENDPOINT',
    'https://us-central1-panoptes-exp.cloudfunctions.net/make-rgb-fits'
)


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

    # Decode the Pub/Sub message.
    pubsub_message = envelope['message']

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        try:
            data = json.loads(
                base64.b64decode(pubsub_message['data']).decode())

        except Exception as e:
            msg = ('Invalid Pub/Sub message: '
                   'data property is not valid base64 encoded JSON')
            print(f'error: {e}')
            return f'Bad Request: {msg}', 400

        # Validate the message is a Cloud Storage event.
        if not data["name"] or not data["bucket"]:
            msg = ('Invalid Cloud Storage notification: '
                   'expected name and bucket properties')
            print(f'error: {msg}')
            return f'Bad Request: {msg}', 400

        try:
            image_received(data)
            # Flush the stdout to avoid log buffering.
            sys.stdout.flush()
            return ('', 204)

        except Exception as e:
            print(f'error: {e}')
            return ('', 500)

    return ('', 500)


def image_received(data):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket.

    FITS: Set header variables and then forward to endpoint for adding headers
    to the metadatabase. The header is looked up from the file id, including the
    storage bucket file generation id, which are stored into the headers.

    CR2: Trigger creation of timelapse and jpg images.

    Example file id:

    panoptes-raw-images/PAN001/14d3bd/20181011T134202/20181011T134333.fits.fz

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """

    bucket_path = data['name']
    object_id = data['id']

    if bucket_path is None:
        return f'No file requested'

    _, file_ext = os.path.splitext(bucket_path)

    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fz,
        '.cr2': process_cr2,
    }

    print(f"Processing {bucket_path}")

    with suppress(KeyError):
        process_lookup[file_ext](bucket_path, object_id)


def process_fz(bucket_path, object_id):
    """ Forward the headers to the -add-header-to-db Cloud Function.

    Args:
        bucket_path (str): The relative (to the bucket) path of the file in the storage bucket.
    """
    # Get some of the fields from the path.
    unit_id, camera_id, seq_time, filename = bucket_path.split('/')

    # Get the image time from the filename
    image_time = filename.split('.')[0]

    # Build the sequence and image ids
    sequence_id = f'{unit_id}_{camera_id}_{seq_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'

    headers = {
        'PANID': unit_id,
        'INSTRUME': camera_id,
        'SEQTIME': seq_time,
        'IMGTIME': image_time,
        'SEQID': sequence_id,
        'IMAGEID': image_id,
        'FILENAME': bucket_path,
        'FILEID': object_id,
        'PSTATE': 'fits_received'
    }

    # Send to add-header-to-db
    print(f"Forwarding to record-image: {headers!r}")
    res = requests.post(add_header_endpoint, json={
        'headers': headers,
        'bucket_path': bucket_path,
        'object_id': object_id,
    })

    if res.ok:
        print(f'Image forwarded to record-image')
    else:
        print(res.text)


def process_fits(bucket_path, object_id):
    """ Forward the headers to the -add-header-to-db Cloud Function.

    Args:
        bucket_path (str): The relative (to the bucket) path of the file in the storage bucket.
    """
    print(f"Forwarding FITS to fits-packer")
    res = requests.post(make_rgb_endpoint, json=dict(bucket_path=bucket_path))

    if res.ok:
        print(f'FITS file packed: {res.json()!r}')
    else:
        print(res.text)


def process_cr2(bucket_path, object_id):
    print(f"Forwarding CR2 to make-rgb-fits")
    res = requests.post(make_rgb_endpoint, json=dict(cr2_file=bucket_path))

    if res.ok:
        print(f'RGB fits files made for {bucket_path}')
    else:
        print(res.text)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=True)
