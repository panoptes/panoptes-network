import os
import sys

import requests
from google.cloud import storage
from panoptes.pipeline.utils.gcp.storage import copy_blob_to_bucket, move_blob_to_bucket
from panoptes.pipeline.utils.metadata import ObservationPathInfo

INCOMING_BUCKET: str = os.getenv('INCOMING_BUCKET', 'panoptes-images-incoming')
OUTGOING_BUCKET: str = os.getenv('OUTGOING_BUCKET', 'panoptes-images-raw')
TIMELAPSE_BUCKET: str = os.getenv('TIMELAPSE_BUCKET', 'panoptes-timelapse')
TEMP_BUCKET: str = os.getenv('TEMP_BUCKET', 'panoptes-images-temp')
JPG_BUCKET: str = os.getenv('JPG_BUCKET', 'panoptes-images-pretty')
ARCHIVE_BUCKET: str = os.getenv('ARCHIVE_BUCKET', 'panoptes-images-archive')

FITS_HEADER_URL: str = os.getenv('FITS_HEADER_URL',
                                 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header')

try:
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
    """Process the raw message """
    attributes = raw_message['attributes']
    print(f"Attributes: {attributes!r}")
    bucket_path = attributes['objectId']

    if bucket_path is None:
        raise Exception(f'No file requested')

    try:
        process_topic(bucket_path)
    except Exception as e:
        print(f'Problem receiving file: {e!r}')

    return True


def process_topic(bucket_path, *args, **kwargs):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket and forwards on to appropriate service.

    This function first check to see if the file has the legacy field name in it,
    and if so rename the file (which will trigger this function again with new name).

    Correct:   PAN001/14d3bd/20200319T111240/20200319T112708.fits.fz
    Legacy:    PAN001/Tess_Sec21_Cam02/14d3bd/20200319T111240/20200319T112708.fits.fz

    Args:
        bucket_path (str): The path to the file in the `panoptes-incoming` bucket.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    # Use bucket path instead of public url
    bucket_path = bucket_path.split(f'{INCOMING_BUCKET}/')[-1]

    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fits,
        '.cr2': process_cr2,
        '.jpg': process_jpg,
        '.mp4': process_timelapse,
    }

    # Remove legacy background files.
    if '-background.fits' in bucket_path:
        print(f'Removing legacy file {bucket_path}')
        incoming_bucket.delete_blob(bucket_path)
        return True

    try:
        path_info = ObservationPathInfo(path=bucket_path)
    except ValueError:
        print(f'Incorrect pattern: UNIT_ID[/FIELD_NAME]/CAMERA_ID/SEQUENCE_TIME/IMAGE_TIME.ext')
        process_unknown(bucket_path)
    else:
        fileext = os.path.splitext(path_info.path)[-1]

        # Rename without field name (which triggers processing again).
        if path_info.field_name != '':
            new_path = str(path_info.as_path(ext=fileext[1:]))
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
    # Archive file.
    copy_blob_to_bucket(bucket_path, incoming_bucket, archive_bucket)

    # Move to raw-image bucket, which triggers image calibration steps.
    move_blob_to_bucket(bucket_path, incoming_bucket, outgoing_bucket)


def process_cr2(bucket_path):
    """Move cr2 to archive and observation bucket"""
    move_blob_to_bucket(bucket_path, incoming_bucket, archive_bucket)


def process_jpg(bucket_path):
    """Move jpgs to observation bucket"""
    move_blob_to_bucket(bucket_path, incoming_bucket, jpg_images_bucket)


def process_timelapse(bucket_path):
    """Move jpgs to observation bucket"""
    move_blob_to_bucket(bucket_path, incoming_bucket, timelapse_bucket)


def process_unknown(bucket_path):
    """Move unknown extensions to the temp bucket."""
    move_blob_to_bucket(bucket_path, incoming_bucket, temp_bucket)


def lookup_fits_header(bucket_path):
    """Read the FITS header from storage. """
    header = None
    request_params = dict(bucket_path=bucket_path, bucket_name=INCOMING_BUCKET)
    res = requests.post(FITS_HEADER_URL, json=request_params)
    if res.ok:
        header = res.json()['header']

    return header
