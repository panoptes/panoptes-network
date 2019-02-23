from os import getenv

import requests

add_header_endpoint = getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/header-to-metadb'
)


def ack_fits_received(data, context):
    """Look for uploaded FITS files and forward them to have headers processed.

    Triggered when file is uploaded to bucket. Checks for FITS and if found will
    set a few header variables and then forward to endpoint for adding headers
    to the metadatabase.

    The header is looked up from the file id, including the storage bucket file
    generation id, which are stored into the headers.

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

    if file_path.endswith('.fz'):

        # Scrub some fields
        print("Processing {}".format(file_path))
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
        requests.post(add_header_endpoint, json={'header': header, 'lookup_file': file_path})
