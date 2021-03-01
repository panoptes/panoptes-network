import os
import base64
import re
import sys
import tempfile

from flask import Flask, request
from google.cloud import exceptions
from google.cloud import firestore
from google.cloud import storage
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.time import current_time

app = Flask(__name__)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')

INCOMING_BUCKET = os.getenv('INCOMING_BUCKET', 'panoptes-images-calibrated')
OUTGOING_BUCKET = os.getenv('INCOMING_BUCKET', 'panoptes-images-processed')
ERROR_BUCKET = os.getenv('ERROR_BUCKET', 'panoptes-images-error')
TIMEOUT = os.getenv('TIMEOUT', 600)

PATH_MATCHER = re.compile(r""".*(?P<unit_id>PAN\d{3})
                                /(?P<camera_id>[a-gA-G0-9]{6})
                                /?(?P<field_name>.*)?
                                /(?P<sequence_time>[0-9]{8}T[0-9]{6})
                                /(?P<image_time>[0-9]{8}T[0-9]{6})
                                \.(?P<fileext>.*)$""",
                          re.VERBOSE)

# Storage
try:
    firestore_db = firestore.Client()
    storage_client = storage.Client()
    incoming_bucket = storage_client.get_bucket(INCOMING_BUCKET)
    outgoing_bucket = storage_client.get_bucket(OUTGOING_BUCKET)
    error_bucket = storage_client.get_bucket(ERROR_BUCKET)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


@app.route("/", methods=["POST"])
def index():
    success = False
    envelope = request.get_json()
    if not envelope:
        msg = "no Pub/Sub message received"
        print(f"error: {msg}")
        return "Invalid pubsub", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        print(f"error: {msg}")
        return "Invalid pubsub", 400

    pubsub_message = envelope["message"]

    try:
        message_data = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
        print(f'Received json {message_data=}')

        # The objectID is stored in the attributes, which is easy to set.
        attributes = pubsub_message["attributes"]
        print(f'Received {attributes=}')

        bucket_path = attributes['objectId']

        new_url = plate_solve(bucket_path)
    except (FileNotFoundError, FileExistsError) as e:
        print(e)
        return '', 204
    except Exception as e:
        print(f'Exception in plate-solve: {e!r}')
        print(f'Raw message {pubsub_message!r}')
        return f'Bad solve: {e!r}', 400
    else:
        # Success
        return f'{new_url}', 204


def plate_solve(bucket_path):
    """Receives the message and process necessary steps.

    Args:
        bucket_path (str): Location of the file in storage bucket.
    """
    # Get information from the path.
    path_match_result = PATH_MATCHER.match(bucket_path)
    unit_id = path_match_result.group('unit_id')
    camera_id = path_match_result.group('camera_id')
    sequence_time = path_match_result.group('sequence_time')
    image_time = path_match_result.group('image_time')
    fileext = path_match_result.group('fileext')

    sequence_id = f'{unit_id}_{camera_id}_{sequence_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'
    print(f'Solving sequence_id={sequence_id} image_id={image_id} for {bucket_path}')

    temp_incoming_fits = tempfile.NamedTemporaryFile(suffix=f'.{fileext}')

    # Blob for plate-solved image.
    outgoing_blob = outgoing_bucket.blob(bucket_path)
    if outgoing_blob.exists():
        # TODO make this smarter?
        raise FileExistsError(f'File has already been processed at {outgoing_blob.public_url}')

    # Blob for calibrated image.
    incoming_blob = incoming_bucket.blob(bucket_path)
    if incoming_blob.exists() is False:
        raise FileNotFoundError(f'File does not exist at location: {incoming_blob.name}')

    print(f'Fetching {incoming_blob.name} to {temp_incoming_fits.name}')
    incoming_blob.download_to_filename(temp_incoming_fits.name)
    print(f'Got file for {bucket_path}')

    image_doc_ref = firestore_db.document(f'images/{image_id}')
    print(f'Got image snapshot from firestore: {image_doc_ref.id}')

    try:
        print(f"Starting plate-solving for FITS file {bucket_path}")
        solve_info = fits_utils.get_solve_field(temp_incoming_fits.name,
                                                skip_solved=False,
                                                timeout=300)
        print(f'Solving completed successfully for {bucket_path}')
        print(f'{bucket_path} solve info: {solve_info}')

        solved_path = solve_info['solved_fits_file']
    except Exception as e:
        # Mark the firestore metadata with error.
        print(f'Error in {bucket_path} plate solve script: {e!r}')
        firestore_db.document(f'images/{image_id}').set(dict(status='error'), merge=True)

        # Move the file to the error bucket.
        try:
            error_blob = incoming_bucket.copy_blob(incoming_blob, error_bucket)
            incoming_blob.delete()
            print(f'Moved error FITS {bucket_path} to {error_blob.public_url}')
        except exceptions.NotFound:
            print(f'Error deleting after error, {bucket_path} blob path not found')
        finally:
            raise Exception('Error solving')

    # Remove old astrometry.net comments.
    print(f'Cleaning FITS headers')
    try:
        solved_header = fits_utils.getheader(temp_incoming_fits.name)
        solved_header.remove('COMMENT', ignore_missing=True, remove_all=True)
        solved_header.add_history(f'Plate-solved at {current_time(pretty=True)}')
        solved_header['SOLVED'] = True
    except Exception as e:
        print(f'Problem cleaning headers: {e!r}')

    #  Upload the plate-solved image.
    print(f'Uploading to {outgoing_blob.public_url}')
    outgoing_blob.upload_from_filename(temp_incoming_fits.name)

    print(f'Recording metadata for {bucket_path}')
    image_doc_updates = dict(
        status='solved',
        plate_solved=True,
        processed_url=outgoing_blob.public_url,
        ra_image=solved_header.get('CRVAL1'),
        dec_image=solved_header.get('CRVAL2'),
    )

    # Record the metadata in firestore.
    image_doc_ref.set(
        image_doc_updates,
        merge=True
    )

    return outgoing_blob.public_url


def move_blob_to_bucket(blob_name, new_bucket, remove=True):
    """Copy the blob from the incoming bucket to the `new_bucket`.

    Args:
        blob_name (str): The relative path to the blob.
        new_bucket (str): The name of the bucket where we move/copy the file.
        remove (bool, optional): If file should be removed afterwards, i.e. a move, or just copied.
            Default True as per the function name.
    """
    print(f'Moving {blob_name} → {new_bucket}')
    incoming_bucket.copy_blob(incoming_bucket.get_blob(blob_name), new_bucket)
    if remove:
        incoming_bucket.delete_blob(blob_name)


def copy_blob_to_bucket(*args, **kwargs):
    kwargs['remove'] = False
    move_blob_to_bucket(*args, **kwargs)
