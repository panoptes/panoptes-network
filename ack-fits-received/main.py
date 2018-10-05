from os import getenv
from google.cloud import storage

import requests

PROJECT_ID = getenv('POSTGRES_USER', 'panoptes')
BUCKET_NAME = getenv('BUCKET_NAME', 'panoptes-survey')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)

add_header_endpoint = getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/header-to-metadb'
)


def ack_fits_received(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function logs relevant data when a file is changed.

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """

    filename = data['name']
    file_id = data['id']  # Includes storage generation

    if filename.endswith('.fz'):
        storage_blob = bucket.get_blob(data['name'])
        header = lookup_fits_header(storage_blob)

        # Scrub some fields
        unit_id, field, camera_id, seq_time, filename = file_id.split('/')

        header['PANID'] = unit_id
        header['FIELD'] = field
        header['FILENAME'] = file_id
        header['PSTATE'] = 'fits_received'

        # Send to add-header-to-db
        print("Sending header for {}".format(file_id))
        requests.post(add_header_endpoint, json={'header': header})


def lookup_fits_header(remote_path):
    """Read the FITS header from storage.

    FITS Header Units are stored in blocks of 2880 bytes consisting of 36 lines
    that are 80 bytes long each. The Header Unit always ends with the single
    word 'END' on a line (not necessarily line 36).

    Here the header is streamed from Storage until the 'END' is found, with
    each line given minimal parsing.

    See https://fits.gsfc.nasa.gov/fits_primer.html for overview of FITS format.

    Args:
        remote_path (`google.cloud.storage.blob.Blob`): Blob or path to remote blob.
            If just the blob name is given then the blob is looked up first.

    Returns:
        dict: FITS header as a dictonary.
    """
    i = 1
    if remote_path.name.endswith('.fz'):
        i = 2  # We skip the compression header info

    headers = dict()

    streaming = True
    while streaming:
        # Get a header card
        start_byte = 2880 * (i - 1)
        end_byte = (2880 * i) - 1
        b_string = remote_path.download_as_string(start=start_byte, end=end_byte)

        # Loop over 80-char lines
        for j in range(0, len(b_string), 80):
            item_string = b_string[j:j + 80].decode()

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

        i += 1

    return headers
