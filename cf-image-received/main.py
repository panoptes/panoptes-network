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

    print("Received: {}".format(data))
    file_path = data['name']
    file_id = data['id']  # Includes bucket & storage generation

    _, file_ext = os.path.splitext(file_path)

    process_lookup = {
        '.fz': process_fits,
        '.cr2': process_cr2,
    }

    process_lookup[file_ext](file_path, file_id)


def process_fits(file_path, file_id):
    # Scrub some fields
    print("Processing {}".format(file_id))
    unit_id, field, camera_id, seq_time, filename = file_path.split('/')

    header = {
        'PANID': unit_id,
        'FIELD': field,
        'FILENAME': file_path,
        'FILEID': file_id,
        'PSTATE': 'fits_received',
    }

    # Send to add-header-to-db
    print("Forwarding to add-header-to-db: {}".format(header))
    requests.post(add_header_endpoint, json={
        'header': header,
        'lookup_file': file_path,
        'file_id': file_id,
    })


def process_cr2(file_path, file_id):
    pass
