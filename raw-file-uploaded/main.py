import base64
import os
import re
import sys
from contextlib import suppress
from enum import IntEnum, auto
from typing import Pattern

import requests
from dateutil.parser import parse as parse_date
from dateutil.tz import UTC
from google.cloud import firestore
from google.cloud import storage


class PipelineStatus(IntEnum):
    RECEIVING = auto()
    RECEIVED = auto()
    CALIBRATING = auto()
    CALIBRATED = auto()
    SOLVING = auto()
    SOLVED = auto()
    MATCHING = auto()
    MATCHED = auto()


CURRENT_STATE: PipelineStatus = PipelineStatus.RECEIVING

INCOMING_BUCKET: str = os.getenv('INCOMING_BUCKET', 'panoptes-images-incoming')
OUTGOING_BUCKET: str = os.getenv('OUTGOING_BUCKET', 'panoptes-images-raw')
TIMELAPSE_BUCKET: str = os.getenv('TIMELAPSE_BUCKET', 'panoptes-timelapse')
TEMP_BUCKET: str = os.getenv('TEMP_BUCKET', 'panoptes-images-temp')
JPG_BUCKET: str = os.getenv('JPG_BUCKET', 'panoptes-images-pretty')
ARCHIVE_BUCKET: str = os.getenv('ARCHIVE_BUCKET', 'panoptes-images-temp')

FITS_HEADER_URL: str = os.getenv('FITS_HEADER_URL',
                                 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header')

PATH_MATCHER: Pattern[str] = re.compile(r""".*(?P<unit_id>PAN\d{3})
                                /(?P<camera_id>[a-gA-G0-9]{6})
                                /?(?P<field_name>.*)?
                                /(?P<sequence_time>[0-9]{8}T[0-9]{6})
                                /(?P<image_time>[0-9]{8}T[0-9]{6})
                                \.(?P<fileext>.*)$""",
                                        re.VERBOSE)

UNIT_FS_KEY: str = os.getenv('UNIT_FS_KEY', 'units')
OBSERVATION_FS_KEY: str = os.getenv('OBSERVATION_FS_KEY', 'observations')
IMAGE_FS_KEY: str = os.getenv('IMAGE_FS_KEY', 'images')

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

        process_topic(bucket_path)
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()

    except Exception as e:
        print(f'error: {e}')


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

    _, file_ext = os.path.splitext(bucket_path)

    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fits,
        '.cr2': process_cr2,
        '.jpg': process_jpg,
        '.mp4': process_timelapse,
    }

    # Check for legacy path: UNIT_ID/FIELD_NAME/CAMERA_ID/SEQUENCE_TIME/IMAGE_TIME
    # Get information from the path.
    path_match_result = PATH_MATCHER.match(bucket_path)
    if path_match_result is None:
        print(f'Incorrect pattern: UNIT_ID[/FIELD_NAME]/CAMERA_ID/SEQUENCE_TIME/IMAGE_TIME.ext')
        process_unknown(bucket_path)
        return

    unit_id = path_match_result.group('unit_id')
    camera_id = path_match_result.group('camera_id')
    field_name = path_match_result.group('field_name')
    sequence_time = path_match_result.group('sequence_time')
    image_time = path_match_result.group('image_time')

    if field_name != '':
        fileext = path_match_result.group('fileext')
        new_path = f'{unit_id}/{camera_id}/{sequence_time}/{image_time}.{fileext}'
        print(f'Removed field name ["{field_name}"], moving: {bucket_path} -> {new_path}')
        incoming_bucket.rename_blob(incoming_bucket.get_blob(bucket_path), new_path)
        return

    sequence_id = f'{unit_id}_{camera_id}_{sequence_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'
    print(f'Recording sequence_id={sequence_id} image_id={image_id} for {bucket_path}')
    try:
        process_lookup[file_ext](bucket_path)
    except KeyError:
        print(f'No handling for {file_ext}, moving to temp bucket')
        process_unknown(bucket_path)


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
            add_records_to_db(bucket_path)
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


def add_records_to_db(bucket_path):
    """Add FITS image info to firestore_db.

    Note:
        This function doesn't check header for proper entries and
        assumes a large list of keywords. See source for details.

    Args:
        header (dict): FITS Header message from an observation.
        bucket_path (str): Full path to the image in a Google Storage Bucket.

    Returns:
        str: The image_id.

    Raises:
        e: Description
    """
    print(f'Recording {bucket_path} metadata.')
    header = lookup_fits_header(bucket_path)
    print(f'Getting sequence_id and image_id from {bucket_path!r}')

    # The above are failing on certain cloud functions for unknown reasons.
    unit_id, camera_id, sequence_time, image_filename = bucket_path.split('/')
    image_time = image_filename.split('.')[0]
    sequence_id = f'{unit_id}_{camera_id}_{sequence_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'

    sequence_time = parse_date(sequence_time).replace(tzinfo=UTC)
    image_time = parse_date(image_time).replace(tzinfo=UTC)

    print(f'Found sequence_id={sequence_id} image_id={image_id}')

    # Scrub all the entries
    for k, v in header.items():
        with suppress(AttributeError):
            header[k] = v.strip()

    print(f'Using headers: {header!r}')
    try:
        print(f'Getting document for observation {sequence_id}')
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

        # Add a units doc if it doesn't exist.
        unit_message = dict(
            name=header.get('OBSERVER', ''),
            location=firestore.GeoPoint(header['LAT-OBS'],
                                        header['LONG-OBS']),
            elevation=float(header.get('ELEV-OBS')),
            status='active'
        )
        unit_doc_ref.set(unit_message, merge=True)

        exptime = header.get('EXPTIME')

        print(f'Making new document for observation {sequence_id}')
        seq_message = dict(
            unit_id=unit_id,
            camera_id=camera_id,
            time=sequence_time,
            exptime=exptime,
            project=header.get('ORIGIN'),
            software_version=header.get('CREATOR', ''),
            field_name=header.get('FIELD', ''),
            iso=header.get('ISO'),
            ra=header.get('CRVAL1'),
            dec=header.get('CRVAL2'),
            status='receiving_files',
            camera_serial_number=header.get('CAMSN'),
            lens_serial_number=header.get('INTSN'),
            num_images=firestore.Increment(1),
            total_exptime=firestore.Increment(exptime),
            received_time=firestore.SERVER_TIMESTAMP)
        print(f"Adding new sequence: {seq_message!r}")
        seq_doc_ref.set(seq_message, merge=True)

        print(f"Adding image document for SEQ={sequence_id} IMG={image_id}")
        measured_rggb = header.get('MEASRGGB').split(' ')

        camera_date = parse_date(header.get('DATE-OBS', '')).replace(tzinfo=UTC)
        file_date = parse_date(header.get('DATE', '')).replace(tzinfo=UTC)

        image_message = dict(
            unit_id=unit_id,
            time=image_time,
            status=PipelineStatus(CURRENT_STATE + 1).name,
            bias_subtracted=False,
            background_subtracted=False,
            plate_solved=False,
            exptime=header.get('EXPTIME'),
            airmass=header.get('AIRMASS'),
            moonfrac=header.get('MOONFRAC'),
            moonsep=header.get('MOONSEP'),
            mount_ha=header.get('HA-MNT'),
            mount_ra=header.get('RA-MNT'),
            mount_dec=header.get('DEC-MNT'),
            camera=dict(
                temp=float(header.get('CAMTEMP').split(' ')[0]),
                colortemp=header.get('COLORTMP'),
                circconf=float(header.get('CIRCCONF').split(' ')[0]),
                measured_ev=header.get('MEASEV'),
                measured_ev2=header.get('MEASEV2'),
                measured_r=float(measured_rggb[0]),
                measured_g1=float(measured_rggb[1]),
                measured_g2=float(measured_rggb[2]),
                measured_b=float(measured_rggb[3]),
                white_lvln=header.get('WHTLVLN'),
                white_lvls=header.get('WHTLVLS'),
                red_balance=header.get('REDBAL'),
                blue_balance=header.get('BLUEBAL'),
                camera_dateobs=camera_date,
                file_creation_date=file_date,
            ),
            received_time=firestore.SERVER_TIMESTAMP
        )
        image_doc_ref.set(image_message, merge=True)

    except Exception as e:
        print(f'Error in adding record: {e!r}')
        raise e

    return True


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


def lookup_fits_header(bucket_path):
    """Read the FITS header from storage. """
    header = None
    request_params = dict(bucket_path=bucket_path, bucket_name=INCOMING_BUCKET)
    res = requests.post(FITS_HEADER_URL, json=request_params)
    if res.ok:
        header = res.json()['header']

    return header
