import os
import sys
import json
import base64
from contextlib import suppress

from google.cloud import pubsub
from google.cloud import storage
from google.cloud import firestore

from dateutil.parser import parse as parse_date

from panoptes.utils import image_id_from_path
from panoptes.utils import sequence_id_from_path
from panoptes.utils.logger import logger

logger.remove()
logger.add(sys.stdout,
           level=os.getenv('LOG_LEVEL', 'INFO'),
           format='{message}',
           colorize=False,
           backtrace=True,
           diagnose=True
           )


FITS_HEADER_URL = os.getenv('FITS_HEADER_URL', 'https://us-central1-panoptes-exp.cloudfunctions.net/get-fits-header')

publisher = pubsub.PublisherClient()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'panoptes-exp')
pubsub_base = f'projects/{project_id}/topics'

plate_solve_topic = os.getenv('SOLVER_topic', 'plate-solve')
make_rgb_topic = os.getenv('RGB_topic', 'make-rgb-fits')

# Storage
storage_client = storage.Client()
storage_bucket = storage_client.get_bucket(os.getenv('BUCKET_NAME', 'panoptes-raw-images'))
timelapse_bucket = storage_client.get_bucket(os.getenv('TIMELAPSE_BUCKET_NAME', 'panoptes-timelapse'))
temp_bucket = storage_client.get_bucket(os.getenv('TEMP_BUCKET_NAME', 'panoptes-temp'))

firestore_db = firestore.Client()


def entry_point(raw_message, context):
    """Background Cloud Function to be triggered by Cloud Storage.

    This will send a pubsub message to a certain topic depending on
    what type of file was uploaded. The servies responsible for those
    topis do all the processing.

    Args:
        message (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    try:
        message = base64.b64decode(raw_message['data']).decode('utf-8')
        attributes = raw_message['attributes']
        logger.debug(f"Message: {message!r} \t Attributes: {attributes!r}")

        process_topic(message, attributes)
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()

    except Exception as e:
        logger.error(f'error: {e}')


def process_topic(message, attributes):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket and forwards on to appropriate service.

    This function first check to see if the file has the legacy field name in it,
    and if so rename the file (which will trigger this function again with new name).

    Correct:   PAN001/14d3bd/20200319T111240/20200319T112708.fits.fz
    Incorrect: PAN001/Tess_Sec21_Cam02/14d3bd/20200319T111240/20200319T112708.fits.fz

    Args:
        message (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    bucket_path = attributes['objectId']

    if bucket_path is None:
        raise Exception(f'No file requested')

    _, file_ext = os.path.splitext(bucket_path)

    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fits,
        '.cr2': process_cr2,
        '.jpg': lambda f: logger.debug(f'Saving {f}'),
    }

    # Check if has legecy path
    path_parts = bucket_path.split('/')
    if len(path_parts) == 5:
        field_name = path_parts.pop(1)
        new_path = '/'.join(path_parts)
        logger.debug(f'Removed field name ["{field_name}"], moving: {bucket_path} -> {new_path}')
        storage_bucket.rename_blob(storage_bucket.get_blob(bucket_path), new_path)
        return

    # Check if invalid extension and move to different bucket.
    if file_ext == '.mp4':
        logger.debug(f'Timelapse. Moving {bucket_path} -> {timelapse_bucket}')
        timelapse_bucket.rename_blob(storage_bucket.get_blob(bucket_path), bucket_path)
        return
    elif file_ext not in list(process_lookup.keys()):
        logger.debug(f'Unhandled extension [{file_ext}]. Moving {bucket_path} -> {temp_bucket}')
        temp_bucket.rename_blob(storage_bucket.get_blob(bucket_path), bucket_path)
        return

    try:
        logger.debug(f"Processing {bucket_path}")
        process_lookup[file_ext](bucket_path)
    except KeyError as e:
        raise Exception(f'No handling for {file_ext}: {e!r}')


def process_fits(bucket_path):
    if 'pointing' not in bucket_path:
        add_records_to_db(bucket_path)
    # try:
    # except Exception as e:
    #     logger.debug(f'Error adding metadata for {bucket_path}: {e!r}')
    # else:
    #     # Continue processing image if metadata insert successful.
    #     send_pubsub_message(plate_solve_topic, dict(bucket_path=bucket_path))


def process_cr2(bucket_path):
    send_pubsub_message(make_rgb_topic, dict(bucket_path=bucket_path))


def add_records_to_db(bucket_path):
    """Add FITS image info to metafirestore_db.

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
    logger.debug(f'Recording {bucket_path} metadata.')

    header = lookup_fits_header(bucket_path)

    image_id = image_id_from_path(bucket_path)
    sequence_id = sequence_id_from_path(bucket_path)

    unit_id, camera_id, sequence_time = sequence_id.split('_')

    # Scrub all the entries
    for k, v in header.items():
        with suppress(AttributeError):
            header[k] = v.strip()

    logger.trace(f'Using headers: {header!r}')
    try:
        unit_id, camera_id, sequence_time = sequence_id.split('_')
        sequence_time = parse_date(sequence_time)

        img_time = parse_date(image_id.split('_')[-1])

        logger.debug(f'Getting document for observation {sequence_id}')
        seq_doc_ref = firestore_db.document(f'observations/{sequence_id}')
        seq_doc_snap = seq_doc_ref.get()

        image_doc_ref = firestore_db.document(f'images/{image_id}')
        image_doc_snap = image_doc_ref.get()

        batch = firestore_db.batch()

        if not seq_doc_snap.exists:
            logger.debug(f'Making new document for observation {sequence_id}')
            # If no sequence doc then probably no unit id. This is just to minimize
            # the number of lookups that would be required if we looked up unit_id
            # doc each time.
            logger.debug(f'Getting doc for unit {unit_id}')
            unit_doc_ref = firestore_db.document(f'units/{unit_id}')
            unit_doc_snap = unit_doc_ref.get()

            # Add a units doc if it doesn't exist.
            if not unit_doc_snap.exists:
                unit_message = {
                    'name': header.get('OBSERVER', ''),
                    'location': firestore.GeoPoint(header['LAT-OBS'], header['LONG-OBS']),
                    'elevation': float(header.get('ELEV-OBS')),
                    'status': 'active'  # Assuming we are active since we received files.
                }
                batch.create(unit_doc_ref, unit_message)

            if not seq_doc_snap.exists:
                seq_message = {
                    'unit_id': unit_id,
                    'camera_id': camera_id,
                    'time': sequence_time,
                    'exptime': header.get('EXPTIME'),
                    'project': header.get('ORIGIN'),  # Project PANOPTES
                    'software_version': header.get('CREATOR', ''),
                    'field_name': header.get('FIELD', ''),
                    'iso': header.get('ISO'),
                    'ra': header.get('CRVAL1'),
                    'dec': header.get('CRVAL2'),
                    'status': 'receiving_files',
                    'received_time': firestore.SERVER_TIMESTAMP,
                }
                logger.debug(f"Adding new sequence: {seq_message!r}")
                batch.create(seq_doc_ref, seq_message)

        if not image_doc_snap.exists:
            logger.debug(f"Adding image document for SEQ={sequence_id} IMG={image_id}")

            image_message = {
                'sequence_id': sequence_id,
                'time': img_time,
                'bucket_path': bucket_path,
                'status': 'received',
                'airmass': header.get('AIRMASS'),
                'exptime': header.get('EXPTIME'),
                'moonfrac': header.get('MOONFRAC'),
                'moonsep': header.get('MOONSEP'),
                'ra_image': header.get('CRVAL1'),
                'dec_image': header.get('CRVAL2'),
                'ha_mnt': header.get('HA-MNT'),
                'ra_mnt': header.get('RA-MNT'),
                'dec_mnt': header.get('DEC-MNT'),
                'received_time': firestore.SERVER_TIMESTAMP
            }
            logger.debug(f'Adding image: {image_message!r}')
            batch.create(image_doc_ref, image_message)

        batch.commit()

    except Exception as e:
        raise e

    return True


def send_pubsub_message(topic, data):
    """Send a pubsub message.

    We send the data as the message body for legacy support
    but also unwrap the dict here to set as attribute as well.
    """
    logger.debug(f"Sending message to {topic}: {data!r}")

    publisher.publish(f'{pubsub_base}/{topic}', json.dumps(data).encode(), **data)


def lookup_fits_header(bucket_path):
    """Read the FITS header from storage.

    FITS Header Units are stored in blocks of 2880 bytes consisting of 36 lines
    that are 80 bytes long each. The Header Unit always ends with the single
    word 'END' on a line (not necessarily line 36).

    Here the header is streamed from Storage until the 'END' is found, with
    each line given minimal parsing.

    See https://fits.gsfc.nasa.gov/fits_primer.html for overview of FITS format.

    Args:
        bucket_path (`google.cloud.storage.blob.Blob`): Blob or path to remote blob.
            If just the blob name is given then the blob is looked up first.

    Returns:
        dict: FITS header as a dictonary.
    """
    card_num = 1
    if bucket_path.endswith('.fz'):
        card_num = 2  # We skip the compression header info card

    headers = dict()

    logger.debug(f'Looking up header for file: {bucket_path}')
    storage_blob = storage_bucket.get_blob(bucket_path)

    streaming = True
    while streaming:
        # Get a header card
        start_byte = 2880 * (card_num - 1)
        end_byte = (2880 * card_num) - 1
        b_string = storage_blob.download_as_string(start=start_byte,
                                                   end=end_byte)

        # Loop over 80-char lines
        for j in range(0, len(b_string), 80):
            item_string = b_string[j: j + 80].decode()

            # End of FITS Header, stop streaming
            if item_string.startswith('END'):
                streaming = False
                break

            # Get key=value pairs (skip COMMENTS and HISTORY)
            if item_string.find('=') > 0:
                k, v = item_string.split('=')

                # Remove FITS comment
                if ' / ' in v:
                    v = v.split(' / ')[0]

                v = v.strip()

                # Cleanup and discover type in dumb fashion
                if v.startswith("'") and v.endswith("'"):
                    v = v.replace("'", "").strip()
                elif v.find('.') > 0:
                    v = float(v)
                elif v == 'T':
                    v = True
                elif v == 'F':
                    v = False
                else:
                    v = int(v)

                headers[k.strip()] = v

        card_num += 1

    return headers
