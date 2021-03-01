import os
import base64
import tempfile
import sys
import re

from google.cloud import firestore
from google.cloud import storage
from astropy.io import fits
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.images import bayer

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
INCOMING_BUCKET = os.getenv('BUCKET_NAME', 'panoptes-images-raw')
OUTGOING_BUCKET = os.getenv('BUCKET_NAME', 'panoptes-images-calibrated')
BACKGROUND_IMAGE_BUCKET = os.getenv('BUCKET_NAME', 'panoptes-images-background')

CAMERA_BIAS = os.getenv('CAMERA_BIAS', 2048.)

PATH_MATCHER = re.compile(r""".*(?P<unit_id>PAN\d{3})
                                /(?P<camera_id>[a-gA-G0-9]{6})
                                /?(?P<field_name>.*)?
                                /(?P<sequence_time>[0-9]{8}T[0-9]{6})
                                /(?P<image_time>[0-9]{8}T[0-9]{6})
                                \.(?P<fileext>fits.*)$""",
                          re.VERBOSE)

# Storage
try:
    firestore_db = firestore.Client()
    storage_client = storage.Client()

    incoming_bucket = storage_client.get_bucket(INCOMING_BUCKET)
    outgoing_bucket = storage_client.get_bucket(OUTGOING_BUCKET)
    bg_image_bucket = storage_client.get_bucket(BACKGROUND_IMAGE_BUCKET)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


def entry_point(raw_message, context):
    """Background Cloud Function to be triggered by Cloud Storage.

    This will send a pubsub message to a certain topic depending on
    what type of file was uploaded. The services responsible for those
    topics do all the processing.

    Args:
        message (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    try:
        message = base64.b64decode(raw_message['data']).decode('utf-8')
        attributes = raw_message['attributes']
        print(f"Message: {message!r} \t Attributes: {attributes!r}")

        bucket_path = attributes['objectId']

        if bucket_path is None:
            raise Exception(f'No file requested')

        subtract_background(bucket_path)

    except (FileNotFoundError, FileExistsError) as e:
        print(e)
    except Exception as e:
        print(f'error: {e}')
    finally:
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()


def subtract_background(bucket_path):
    """Calculate the RGB background for a Bayer array FITS image. """
    # If the image_bucket path is a public https url,
    # get just the relative path for looking up in image_bucket.
    try:
        bucket_path = bucket_path.replace('https://storage.googleapis.com/panoptes-raw-images/', '')
    except AttributeError as e:
        print(f'Problem with bucket_path={bucket_path}: {e!r}')
    bg_output_path = bucket_path.replace('.fits.fz', '-rgb-bg.fits')

    path_match_result = PATH_MATCHER.match(bucket_path)
    image_id = '{}_{}_{}'.format(
        path_match_result.group('unit_id'),
        path_match_result.group('camera_id'),
        path_match_result.group('image_time'),
    )

    image_doc_ref = firestore_db.document(f'images/{image_id}')
    print(f'Got image snapshot from firestore')

    # Get blob objects form bucket.
    incoming_blob = incoming_bucket.get_blob(bucket_path)
    outgoing_blob = outgoing_bucket.blob(bucket_path.replace('.fz', ''))
    bg_blob = bg_image_bucket.blob(bg_output_path)

    paths = {
        'reduced': outgoing_blob.public_url,
        'background': bg_blob.public_url,
        'original': incoming_blob.public_url
    }

    if outgoing_blob.exists() and bg_blob.exists():
        raise FileExistsError(f'Both the background and calibrated file already exist: {paths!r}')

    # Need a valid image.
    if incoming_blob.exists() is False:
        raise FileNotFoundError(f'No image at {bucket_path}, nothing to do')

    # Temp file paths for holding data.
    temp_incoming_path = tempfile.NamedTemporaryFile()
    temp_outgoing_path = tempfile.NamedTemporaryFile()
    temp_bg_path = tempfile.NamedTemporaryFile()

    # Get the raw data.
    incoming_blob.download_to_filename(temp_incoming_path.name)
    data, header = fits_utils.getdata(temp_incoming_path.name, header=True)

    # Bias subtract if asked.
    if CAMERA_BIAS > 0:
        print(f'Subtracting {CAMERA_BIAS=} from data')
        data = data - CAMERA_BIAS

    # Get RGB background data.
    rgb_bg_data = bayer.get_rgb_background(data=data, return_separate=True)

    # Save the RGB data to a FITS file.
    # TODO fpack the files? They are big without, but not really used.
    #  Can't be done in Cloud Function easily.
    background_path = bayer.save_rgb_bg_fits(rgb_bg_data,
                                             temp_bg_path.name,
                                             header=header,
                                             fpack=False)

    # Get the background map from the file.
    combined_bg_map = fits_utils.getdata(background_path, ext=1)

    # Subtract background from the data.
    print(f'Creating reduced FITS file')
    reduced_data = data - combined_bg_map

    # Headers to mark processing status.
    header['BIASSUB'] = True
    header['BGSUB'] = True

    # Save the reduced data.
    primary = fits.PrimaryHDU(reduced_data, header=header)
    primary.scale('int16')
    fits.HDUList([primary]).writeto(temp_outgoing_path.name)
    # TODO fpack calibrated file as well.

    # Upload background and reduced FITS.
    print(f'Uploading background FITS file to {bg_blob.public_url}')
    bg_blob.upload_from_filename(background_path)

    print(f'Uploading calibrated FITS file to {outgoing_blob.public_url}')
    outgoing_blob.upload_from_filename(temp_outgoing_path.name)

    print(f'Recording metadata for {bucket_path}')
    image_doc_updates = dict(
        status='calibrated',
        bias_subtracted=True,
        background_subtracted=True,
        background_file=bg_blob.public_url,
        calibrated_url=outgoing_blob.public_url,
    )

    # Record the metadata in firestore.
    image_doc_ref.set(
        image_doc_updates,
        merge=True
    )
