import os
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

    file_path = data['name']
    file_id = data['id']  # Includes bucket & storage generation
    print(f"Received: {file_id} at {file_path}")

    _, file_ext = os.path.splitext(file_path)

    process_lookup = {
        '.fz': process_fits,
        '.cr2': process_cr2,
    }

    print(f"Processing {file_id}")
    process_lookup[file_ext](file_path, file_id)


def process_fits(file_path, file_id):
    """ Thin-wrapper around process_file that sets PIAA_STATE """
    headers = {
        'PIAA_STATE': 'fits_received'
    }
    process_file(file_path, file_id, headers)


def process_cr2(file_path, file_id):
    """ Thin-wrapper around process_file that sets PIAA_STATE """
    headers = {
        'PIAA_STATE': 'cr2_received'
    }
    process_file(file_path, file_id, headers)


def process_file(file_path, file_id, headers):
    """ Forward the headers to the -add-header-to-db Cloud Function.

    Args:
        file_path (str): The relative (to the bucket) path of the file in the storage bucket.
        file_id (str): The full blob id for the file in the storage bucket, includes generation.
        headers (dict): A dictionary of header values to be stored with header values from image.
    """
    # Get some of the fields from the path.
    unit_id, field, camera_id, seq_time, filename = file_path.split('/')

    headers.update({
        'PANID': unit_id,
        'FIELD': field,
        'FILENAME': file_path,
        'FILEID': file_id,
    })

    # Send to add-header-to-db
    print(f"Forwarding to add-header-to-db: {headers!r}")
    requests.post(add_header_endpoint, json={
        'headers': headers,
        'bucket_path': file_path,
        'object_id': file_id,
    })
