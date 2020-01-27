import os
import rawpy
from copy import copy
from contextlib import suppress

from flask import jsonify
from google.cloud import storage

from astropy.io import fits

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')
UPLOAD_BUCKET = os.getenv('UPLOAD_BUCKET', 'panoptes-rgb-images')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)

TMP_DIR = '/tmp'

DEFAULT_RAWPY_OPTIONS = {
    "demosaic_algorithm": rawpy.DemosaicAlgorithm.AAHD,
    "no_auto_bright": True,
    "output_bps": 16,  # 16 bit
    "half_size": True,
    "gamma": (1, 1),  # Linear
}


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
            data = json.loads(
                base64.b64decode(pubsub_message['data']).decode())

        except Exception as e:
            msg = ('Invalid Pub/Sub message: '
                   'data property is not valid base64 encoded JSON')
            print(f'error: {e}')
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
    """Responds to any HTTP request.

    Notes:
        rawpy params: https://letmaik.github.io/rawpy/api/rawpy.Params.html
        rawpy enums: https://letmaik.github.io/rawpy/api/enums.html

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    raw_file = data.get('bucket_path')

    # Get default rawpy options
    rawpy_options = copy(DEFAULT_RAWPY_OPTIONS)
    # Update rawpy options with those passed by user
    with suppress(KeyError):
        rawpy_options.update(request_json['rawpy_options'])

    print(f'Using rawpy options')
    print(f'{rawpy_options}')

    fits_file = raw_file.replace('.cr2', '.fits.fz')

    print(f'CR2 File: {raw_file}')
    print(f'FITS File: {fits_file}')

    # Download the file locally
    base_dir = os.path.dirname(raw_file)
    base_fn = os.path.basename(raw_file)
    base_name, ext = os.path.splitext(base_fn)

    print('Getting CR2 file')
    cr2_storage_blob = bucket.get_blob(raw_file)
    tmp_fn = os.path.join(TMP_DIR, base_fn)
    print(f'Downloading to {tmp_fn}')
    cr2_storage_blob.download_to_filename(tmp_fn)

    # local_fits_file = cr2_storage_blob.download_to_filename(base_fn.replace('.cr2', '.fits.fz')

    # Read in with rawpy
    print(f'Opening via rawpy')
    try:
        with rawpy.imread(tmp_fn) as raw:
            d0 = raw.postprocess(**rawpy_options)
            print(f'Got raw data: {d0.shape}')

            # header = fits.getheader(raw_file.replace('.cr2', '.fits))
            print(f'Looping through the colors')
            for color, i in zip('rgb', range(3)):
                c0 = d0[:, :, i]
                hdul = fits.PrimaryHDU(data=c0)

                fn_out = f'{base_name}_{color}.fits'
                fn_path = os.path.join(TMP_DIR, fn_out)

                print(f'Writing {fn_out}')
                hdul.writeto(fn_path, overwrite=True)

                # Upload
                print(f"Sending {fn_out} to temp bucket")
                try:
                    bucket_fn = os.path.join(base_dir, fn_out)
                    upload_blob(fn_path, bucket_fn)
                finally:
                    print(f'Removing {fn_out}')
                    os.remove(fn_path)
    finally:
        print(f'Removing {tmp_fn}')
        os.remove(tmp_fn)

    return jsonify(success=True, msg=f"RGB FITS files made for {raw_file}")


def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = client.get_bucket(UPLOAD_BUCKET)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))
