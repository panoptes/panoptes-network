import os
from Flask import jsonify
from contextlib import suppress

import requests

add_header_endpoint = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/header-to-db'
)


def image_received(request):
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
    request_json = request.get_json()
    if request.args and 'bucket_path' in request.args:
        bucket_path = request.args.get('bucket_path')
    elif request_json and 'bucket_path' in request_json:
        bucket_path = request_json['bucket_path']
    else:
        return f'No file requested'

    _, file_ext = os.path.splitext(bucket_path)

    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fits,
        '.cr2': process_cr2,
    }

    print(f"Processing {bucket_path}")

    with suppress(KeyError):
        process_lookup[file_ext](bucket_path)

    return jsonify(success=True, msg=f"Image processed: {bucket_path}")


def process_fits(bucket_path):
    """ Forward the headers to the -add-header-to-db Cloud Function.

    Args:
        bucket_path (str): The relative (to the bucket) path of the file in the storage bucket.
    """
    # Get some of the fields from the path.
    unit_id, field, camera_id, seq_time, filename = bucket_path.split('/')

    # Get the image time from the filename
    image_time = filename.split('.')[0]

    # Build the sequence and image ids
    sequence_id = f'{unit_id}_{camera_id}_{seq_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'

    headers = {
        'PANID': unit_id,
        'FIELD': field,
        'INSTRUME': camera_id,
        'SEQTIME': seq_time,
        'IMGTIME': image_time,
        'SEQID': sequence_id,
        'IMAGEID': image_id,
        'FILENAME': bucket_path,
        'PSTATE': 'fits_received'
    }

    # Send to add-header-to-db
    print(f"Forwarding to add-header-to-db: {headers!r}")
    requests.post(add_header_endpoint, json={
        'headers': headers,
        'bucket_path': bucket_path,
    })


def process_cr2():
    print('TODO: ADD CR2 PROCESSING')
