import base64
import os
import re
import sys
import tempfile
from contextlib import suppress
from enum import IntEnum, auto
from typing import Union, Pattern, Tuple

import numpy as np
from astropy.io import fits
from google.cloud import firestore
from google.cloud import storage
from panoptes.utils.images import bayer
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.serializers import to_json


class PipelineStatus(IntEnum):
    RECEIVING = auto()
    RECEIVED = auto()
    CALIBRATING = auto()
    CALIBRATED = auto()
    SOLVING = auto()
    SOLVED = auto()
    MATCHING = auto()
    MATCHED = auto()


CURRENT_STATE: PipelineStatus = PipelineStatus.CALIBRATING

INCOMING_BUCKET: str = os.getenv('INCOMING_BUCKET', 'panoptes-images-raw')
OUTGOING_BUCKET: str = os.getenv('OUTGOING_BUCKET', 'panoptes-images-calibrated')
BACKGROUND_IMAGE_BUCKET: str = os.getenv('BACKGROUND_BUCKET', 'panoptes-images-background')

UNIT_FS_KEY: str = os.getenv('UNIT_FS_KEY', 'units')
OBSERVATION_FS_KEY: str = os.getenv('OBSERVATION_FS_KEY', 'observations')
IMAGE_FS_KEY: str = os.getenv('IMAGE_FS_KEY', 'images')

CAMERA_BIAS: Union[int, float] = os.getenv('CAMERA_BIAS', 2048.)
BG_PARAMS_BOX_SIZE: Tuple[int, int] = os.getenv('BG_PARAMS_BOX_SIZE', (79, 84))  # (11, 12)
BG_PARAMS_FILTER_SIZE: Tuple[int, int] = os.getenv('BG_PARAMS_BOX_SIZE', (11, 12))  # (11, 12)

PATH_MATCHER: Pattern[str] = re.compile(r""".*(?P<unit_id>PAN\d{3})
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

        background_params = attributes.get('background_params', {
            'box_size': BG_PARAMS_BOX_SIZE,
            'filter_size': BG_PARAMS_FILTER_SIZE,
        })

        subtract_background(bucket_path, background_params)

    except (FileNotFoundError, FileExistsError) as e:
        print(e)
    except Exception as e:
        print(f'error: {e}')
    finally:
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()


def subtract_background(bucket_path, background_params=None):
    """Calculate the RGB background for a Bayer array FITS image. """
    # If the image_bucket path is a public https url,
    # get just the relative path for looking up in image_bucket.
    background_params = background_params or dict()
    try:
        bucket_path = bucket_path.replace('https://storage.googleapis.com/panoptes-raw-images/', '')
    except AttributeError as e:
        print(f'Problem with bucket_path={bucket_path}: {e!r}')
    bg_output_path = bucket_path.replace('.fits.fz', '-rgb-bg.fits')

    # Get information from the path.
    path_match_result = PATH_MATCHER.match(bucket_path)
    unit_id = path_match_result.group('unit_id')
    camera_id = path_match_result.group('camera_id')
    sequence_time = path_match_result.group('sequence_time')
    image_time = path_match_result.group('image_time')

    sequence_id = f'{unit_id}_{camera_id}_{sequence_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'
    print(f'Calibrating sequence_id={sequence_id} image_id={image_id} for {bucket_path}')

    unit_doc_ref = firestore_db.document(f'{UNIT_FS_KEY}/{unit_id}')
    seq_doc_ref = unit_doc_ref.collection(OBSERVATION_FS_KEY).document(sequence_id)
    image_doc_ref = seq_doc_ref.collection(IMAGE_FS_KEY).document(image_id)

    with suppress(KeyError, TypeError):
        image_status = image_doc_ref.get(['status']).to_dict()['status']
        if PipelineStatus[image_status] >= CURRENT_STATE:
            print(f'Skipping image with status of {PipelineStatus[image_status].name}')
            return True

    print(f'Setting image {image_doc_ref.id} to {CURRENT_STATE.name}')
    image_doc_ref.set(dict(status=CURRENT_STATE.name), merge=True)

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
    rgb_bg_data = bayer.get_rgb_background(data=data, return_separate=True, **background_params)

    # Clean out the headers
    header.remove('COMMENT', ignore_missing=True, remove_all=True)
    header.remove('HISTORY', ignore_missing=True, remove_all=True)

    # Save the RGB data to a FITS file.
    # TODO fpack the files? They are big without, but not really used.
    #  Can't be done in Cloud Function easily.
    combined_bg = save_rgb_bg_fits(rgb_bg_data, temp_bg_path.name, header=header)

    # Subtract background from the data.
    reduced_data = (data - combined_bg).astype(np.float32)

    # Headers to mark processing status.
    header['BIASSUB'] = True
    header['BGSUB'] = True
    header['BGPARAMS'] = to_json(background_params)
    header['CAMBIAS'] = CAMERA_BIAS

    # Save the reduced data.
    print(f'Creating reduced FITS file')
    primary = fits.PrimaryHDU(reduced_data, header=header)
    fits.HDUList([primary]).writeto(temp_outgoing_path.name)
    # TODO fpack calibrated file as well.

    # Upload background and reduced FITS.
    print(f'Uploading background FITS file to {bg_blob.public_url}')
    bg_blob.upload_from_filename(temp_bg_path.name)

    print(f'Uploading calibrated FITS file to {outgoing_blob.public_url}')
    outgoing_blob.upload_from_filename(temp_outgoing_path.name)

    print(f'Recording metadata for {bucket_path}')
    image_doc_updates = dict(
        status=PipelineStatus(CURRENT_STATE + 1).name,
        bias_subtracted=True,
        background_subtracted=True,
        camera_bias=CAMERA_BIAS,
        background_params=background_params,
        background_url=bg_blob.public_url,
        calibrated_url=outgoing_blob.public_url,
    )

    # Record the metadata in firestore.
    image_doc_ref.set(
        image_doc_updates,
        merge=True
    )


def save_rgb_bg_fits(rgb_bg_data, output_filename, header=None):
    # Get the background map from the file.
    combined_bg = np.ma.array([np.ma.array(data=d.background, mask=d.mask)
                               for d in rgb_bg_data]).sum(0).filled(0).astype(np.float32)

    header = header or fits.Header()

    # Combined background is primary hdu.
    primary = fits.PrimaryHDU(combined_bg, header=header)
    hdu_list = [primary]

    for color, bg in zip(bayer.RGB, rgb_bg_data):
        h0 = fits.Header()
        h0['COLOR'] = f'{color.name.lower()}'

        h0['IMGTYPE'] = 'background'
        img0 = fits.ImageHDU(bg.background, header=h0)
        hdu_list.append(img0)

        h0['IMGTYPE'] = 'background_rms'
        img1 = fits.ImageHDU(bg.background_rms, header=h0)
        hdu_list.append(img1)

    hdul = fits.HDUList(hdu_list)
    hdul.writeto(output_filename, overwrite=True)

    return combined_bg
