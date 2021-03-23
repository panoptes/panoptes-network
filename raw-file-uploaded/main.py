import os
import sys

import requests
from google.cloud import firestore
from google.cloud import storage
from panoptes.pipeline.cloud.handler import Handler
from panoptes.pipeline.utils.gcp.storage import copy_blob_to_bucket, move_blob_to_bucket
from panoptes.pipeline.utils.metadata import ObservationPathInfo, record_metadata

INCOMING_BUCKET: str = os.getenv('INCOMING_BUCKET', 'panoptes-images-incoming')
OUTGOING_BUCKET: str = os.getenv('OUTGOING_BUCKET', 'panoptes-images-raw')
TIMELAPSE_BUCKET: str = os.getenv('TIMELAPSE_BUCKET', 'panoptes-timelapse')
TEMP_BUCKET: str = os.getenv('TEMP_BUCKET', 'panoptes-images-temp')
JPG_BUCKET: str = os.getenv('JPG_BUCKET', 'panoptes-images-pretty')
ARCHIVE_BUCKET: str = os.getenv('ARCHIVE_BUCKET', 'panoptes-images-temp')

FITS_HEADER_URL: str = os.getenv('FITS_HEADER_URL',
                                 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header')

try:
    firestore_db = firestore.Client()

    # Storage
    sc = storage.Client()
    incoming_bucket = sc.get_bucket(INCOMING_BUCKET)
    outgoing_bucket = sc.get_bucket(OUTGOING_BUCKET)
    timelapse_bucket = sc.get_bucket(TIMELAPSE_BUCKET)
    temp_bucket = sc.get_bucket(TEMP_BUCKET)
    archive_bucket = sc.get_bucket(ARCHIVE_BUCKET)
    jpg_images_bucket = sc.get_bucket(JPG_BUCKET)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


def entry_point(raw_message, context):
    """Process the raw message and """
    Handler.cloud_function_entry_point(raw_message, context, operation=process_topic)


def process_topic(bucket_path):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket and forwards on to appropriate service.

    This function first check to see if the file has the legacy field name in it,
    and if so rename the file (which will trigger this function again with new name).

    Correct:   PAN001/14d3bd/20200319T111240/20200319T112708.fits.fz
    Incorrect: PAN001/Tess_Sec21_Cam02/14d3bd/20200319T111240/20200319T112708.fits.fz

    Args:
        bucket_path (str): The path to the file in the `panoptes-incoming` bucket.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fits,
        '.cr2': process_cr2,
        '.jpg': process_jpg,
        '.mp4': process_timelapse,
    }

    try:
        path_info = ObservationPathInfo(path=bucket_path)
    except ValueError:
        print(f'Incorrect pattern: UNIT_ID[/FIELD_NAME]/CAMERA_ID/SEQUENCE_TIME/IMAGE_TIME.ext')
        process_unknown(bucket_path)
    else:
        fileext = os.path.splitext(path_info.path)[-1]

        # Rename without field name (which triggers processing again).
        if path_info.field_name != '':
            new_path = path_info.as_path(ext=fileext)
            print(f'Removed {path_info.field_name!r}, moving: {bucket_path} -> {new_path}')
            incoming_bucket.rename_blob(incoming_bucket.get_blob(bucket_path), new_path)
            return False

        try:
            print(f'Recording {path_info.id} for {bucket_path}')
            process_lookup[fileext](bucket_path)
        except KeyError:
            print(f'No handling for {fileext!r}, moving to temp bucket')
            process_unknown(bucket_path)
            return False

        return True


def process_fits(bucket_path):
    """Record and move the FITS images.

    Record the metadata for all observation images in the firestore db. Move a copy
    of the image to the archive bucket as well as to the observations bucks.

    Skip recording the metadata for the pointing images but still move them.

    Args:
        bucket_path (str): The relative path in a google storage bucket.
    """
    try:
        if 'pointing' not in bucket_path:
            header = lookup_fits_header(bucket_path)
            record_metadata(bucket_path, header, firestore_db=firestore.Client())
    except Exception as e:
        print(f'Error adding firestore record for {bucket_path}: {e!r}')
    else:
        # Archive file.
        copy_blob_to_bucket(bucket_path, archive_bucket)

        # Move to raw-image bucket, which triggers background subtraction.
        move_blob_to_bucket(bucket_path, outgoing_bucket)


def process_cr2(bucket_path):
    """Move cr2 to archive and observation bucket"""
    copy_blob_to_bucket(bucket_path, archive_bucket)
    move_blob_to_bucket(bucket_path, outgoing_bucket)


def process_jpg(bucket_path):
    """Move jpgs to observation bucket"""
    move_blob_to_bucket(bucket_path, jpg_images_bucket)


def process_timelapse(bucket_path):
    """Move jpgs to observation bucket"""
    move_blob_to_bucket(bucket_path, timelapse_bucket)


def process_unknown(bucket_path):
    """Move unknown extensions to the temp bucket."""
    move_blob_to_bucket(bucket_path, temp_bucket)


def lookup_fits_header(bucket_path):
    """Read the FITS header from storage. """
    header = None
    request_params = dict(bucket_path=bucket_path, bucket_name=INCOMING_BUCKET)
    res = requests.post(FITS_HEADER_URL, json=request_params)
    if res.ok:
        header = res.json()['header']

    return header
