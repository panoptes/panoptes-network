import base64
import os
import sys

import pandas as pd

BASE_URL = os.getenv('BASE_URL', 'https://storage.googleapis.com/panoptes-observations/')


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
        print(f"Message: {message!r} \t Attributes: {attributes!r}")

        process_topic(message, attributes)
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()

    except Exception as e:
        print(f'error: {e}')


def process_topic(message, attributes):
    """Look for uploaded files and process according to the file type.

    Args:
        attributes (dict): The message attributes.
        message (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    bucket_path = attributes['objectId']

    if bucket_path is None:
        raise Exception(f'No file requested')

    df = pd.read_csv(bucket_path)

    table = None
    if 'sources' in bucket_path:
        table = 'sources'
        # TODO make sequence_id_from_path work here.
        df['sequence_id'] = bucket_path.split('/')[-1].split('-')[0]

    if 'metadata' in bucket_path:
        table = 'metadata'
        columns = [
            'unit_id',
            'sequence_id',
            'image_id',
            'time',
            'exptime',
            'airmass',
            'ra_image',
            'dec_image',
            'ra_mnt',
            'ha_mnt',
            'dec_mnt',
            'moonsep',
            'moonfrac',
            'bucket_path',
            'public_url'
        ]
        df = df[columns]

    if not table:
        print(f'No table given in {bucket_path}')

    print(f'Sending {len(df)} rows to observations.{table}')
    df.convert_dtypes().to_gbq(
        f'observations.{table}',
        project_id='panoptes-exp',
        if_exists='append'
    )
