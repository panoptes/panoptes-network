import os
import re
from os import getenv

import requests

add_header_endpoint = getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/header-to-metadb'
)


def ack_image_received(data, context):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket.

    FITS: Set header variables and then forward to endpoint for adding headers
    to the metadatabase. The header is looked up from the file id, including the
    storage bucket file generation id, which are stored into the headers.

    CR2: Trigger creation of timelapse and jpg images.

    Example file id:

    panoptes-survey/PAN001/M42/14d3bd/20181011T134202/20181011T134333.fits.fz/1539272833023747

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """

    bucket_path = data['name']
    object_id = data['id']  # Includes bucket & storage generation
    print(f"Received: {object_id} at {bucket_path}")

    _, file_ext = os.path.splitext(bucket_path)

    process_lookup = {
        '.fz': process_fits,
        '.cr2': process_cr2,
    }

    print(f"Processing {object_id}")
    process_lookup[file_ext](bucket_path, object_id)


def process_fits(bucket_path, object_id):
    """ Thin-wrapper around process_file that sets PIAA_STATE """
    headers = {
        'PSTATE': 'fits_received'
    }
    process_file(bucket_path, object_id, headers)


def process_cr2(bucket_path, object_id):
    pass


def process_file(bucket_path, object_id, headers):
    """ Forward the headers to the -add-header-to-db Cloud Function.

    Args:
        bucket_path (str): The relative (to the bucket) path of the file in the storage bucket.
        object_id (str): The full blob id for the file in the storage bucket, includes generation.
        headers (dict): A dictionary of header values to be stored with header values from image.
    """
    # Get some of the fields from the path.
    unit_id, field, camera_id, seq_time, filename = bucket_path.split('/')

    # Get the image time from the filename
    image_time = filename.split('.')[0]

    # Build the sequence and image ids
    sequence_id = f'{unit_id}_{camera_id}_{seq_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'

    headers.update({
        'PANID': unit_id,
        'FIELD': field,
        'INSTRUME': camera_id,
        'SEQTIME': seq_time,
        'IMGTIME': image_time,
        'SEQID': sequence_id,
        'IMAGEID': image_id,
        'FILENAME': bucket_path,
        'FILEID': object_id,
    })

    # Send to add-header-to-db
    print(f"Forwarding to add-header-to-db: {headers!r}")
    requests.post(add_header_endpoint, json={
        'headers': headers,
        'bucket_path': bucket_path,
        'object_id': object_id,
    })
