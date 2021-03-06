import base64
import os
import sys
import tempfile
from contextlib import suppress

from flask import Flask, request
from google.cloud import exceptions
from google.cloud import firestore
from google.cloud import storage
from panoptes.pipeline.utils.metadata import ObservationPathInfo
from panoptes.pipeline.utils.status import ImageStatus
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.time import current_time

CURRENT_STATE: ImageStatus = ImageStatus.SOLVING

app = Flask(__name__)

INCOMING_BUCKET: str = os.getenv('INCOMING_BUCKET', 'panoptes-images-calibrated')
OUTGOING_BUCKET: str = os.getenv('OUTGOING_BUCKET', 'panoptes-images-solved')
ERROR_BUCKET: str = os.getenv('ERROR_BUCKET', 'panoptes-images-error')
TIMEOUT: int = os.getenv('TIMEOUT', 600)

UNIT_FS_KEY: str = os.getenv('UNIT_FS_KEY', 'units')
OBSERVATION_FS_KEY: str = os.getenv('OBSERVATION_FS_KEY', 'observations')
IMAGE_FS_KEY: str = os.getenv('IMAGE_FS_KEY', 'images')

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

        url = plate_solve(bucket_path)
    except (FileNotFoundError, FileExistsError) as e:
        print(e)
        return '', 204
    except Exception as e:
        print(f'Exception in plate-solve: {e!r}')
        return f'Incorrect solve, file moved to error bucket', 204
    else:
        # Success
        return f'{url}', 204


def plate_solve(bucket_path):
    """Receives the message and process necessary steps.

    Args:
        bucket_path (str): Location of the file in storage bucket.
    """
    # Get information from the path.
    path_info = ObservationPathInfo(path=bucket_path)
    unit_id = path_info.unit_id
    camera_id = path_info.camera_id
    sequence_time = path_info.sequence_time
    image_time = path_info.image_time
    fileext = path_info.fileext

    sequence_id = path_info.sequence_id
    image_id = path_info.image_id
    print(f'Solving sequence_id={sequence_id} image_id={image_id} for {bucket_path}')

    unit_doc_ref = firestore_db.document((f'{UNIT_FS_KEY}/{unit_id}',))
    seq_doc_ref = unit_doc_ref.collection(OBSERVATION_FS_KEY).document(sequence_id)
    image_doc_ref = seq_doc_ref.collection(IMAGE_FS_KEY).document(image_id)

    with suppress(KeyError, TypeError):
        image_status = image_doc_ref.get(['status']).to_dict()['status']
        if ImageStatus[image_status] >= CURRENT_STATE:
            print(f'Skipping image with status of {ImageStatus[image_status].name}')
            return True

    print(f'Setting image {image_doc_ref.id} to {CURRENT_STATE.name}')
    image_doc_ref.set(dict(status=CURRENT_STATE.name), merge=True)

    temp_incoming_fits = tempfile.NamedTemporaryFile(suffix=f'.{fileext}')

    # Blob for plate-solved image.
    outgoing_blob = outgoing_bucket.blob(bucket_path)

    # TODO need to trigger the lookup-catalog-sources here. For now just re-solve
    # if outgoing_blob.exists():
    # raise FileExistsError(f'File has already been processed at {outgoing_blob.public_url}')

    # Blob for calibrated image.
    incoming_blob = incoming_bucket.blob(bucket_path)
    if incoming_blob.exists() is False:
        raise FileNotFoundError(f'File does not exist at location: {incoming_blob.name}')

    print(f'Fetching {incoming_blob.name} to {temp_incoming_fits.name}')
    incoming_blob.download_to_filename(temp_incoming_fits.name)
    print(f'Got file for {bucket_path}')

    try:
        print(f"Starting plate-solving for FITS file {bucket_path}")
        solve_info = fits_utils.get_solve_field(temp_incoming_fits.name,
                                                skip_solved=False,
                                                timeout=300)
        print(f'Solving completed successfully for {bucket_path}')
        print(f'{bucket_path} solve info: {solve_info}')
    except Exception as e:
        # Mark the firestore metadata with error.
        print(f'Error in {bucket_path} plate solve script: {e!r}')
        image_doc_ref.set(dict(status='error'), merge=True)

        # Move the file to the error bucket.
        try:
            error_blob = incoming_bucket.copy_blob(incoming_blob, error_bucket)
            incoming_blob.delete()
            print(f'Moved error FITS {bucket_path} to {error_blob.public_url}')
        except exceptions.NotFound:
            print(f'Error deleting after error, {bucket_path} blob path not found')
        finally:
            raise Exception('Error solving')

    solved_header = fits_utils.getheader(temp_incoming_fits.name)

    print(f'Cleaning FITS headers')
    try:
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
        status=ImageStatus(CURRENT_STATE + 1).name,
        plate_solved=True,
        solved_url=outgoing_blob.public_url,
        ra_image=solved_header.get('CRVAL1'),
        dec_image=solved_header.get('CRVAL2'),
    )

    # Record the metadata in firestore.
    image_doc_ref.set(
        image_doc_updates,
        merge=True
    )

    return outgoing_blob.public_url
