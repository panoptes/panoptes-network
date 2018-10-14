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

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """

    filename = data['name']
    file_id = data['id']  # Includes storage generation

    if filename.endswith('.fz'):

        # Scrub some fields
        unit_id, field, camera_id, seq_time, filename = file_id.split('/')

        header = {
            'PANID': unit_id,
            'FIELD': field,
            'FILENAME': file_id,
            'PSTATE': 'fits_received',
        }

        # Send to add-header-to-db
        print("Forwarding to add-header-to-db: {}".format(file_id))
        requests.post(add_header_endpoint, json={'header': header, 'lookup_file': filename})
