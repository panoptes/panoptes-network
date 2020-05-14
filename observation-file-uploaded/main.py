import base64
import json
import os
import sys

import pandas as pd
from google.cloud import bigquery
from google.cloud import storage

BASE_URL = os.getenv('BASE_URL', 'https://storage.googleapis.com/panoptes-observations/')

bq_client = bigquery.Client()
storage_client = storage.Client()


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
        message = json.loads(base64.b64decode(raw_message['data']).decode('utf-8'))
        attributes = raw_message['attributes']
        print(f"Message: {message!r} \t Attributes: {attributes!r}")

        process_topic(message, attributes)
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()

    except Exception as e:
        print(f'Error: {e!r}')


def process_topic(message, attributes):
    """Look for uploaded files and process according to the file type.

    Args:
        message (dict): The Cloud Functions event payload.
        attributes (dict): The message attributes.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    bucket = attributes['bucketId']
    bucket_path = attributes['objectId']
    bucket_link = message['mediaLink']

    # Only do it for new files.
    if 'overwroteGeneration' in attributes:
        print(f'File already exists in bucket, skipping import for {bucket_link}')
        return

    if bucket_path is None:
        raise Exception(f'No file requested')

    print(f'Looking up {bucket_link}')

    try:
        _, file_ext = os.path.splitext(bucket_path)
        # Make sure to skip the period in the extension.
        read_func = getattr(pd, f'read_{file_ext[1:]}')
        df = read_func(bucket_link)
    except Exception as e:
        print(f'Error with lookup: {e!r}')
        return

    bq_table = None
    if 'sources' in bucket_path:
        bq_table = 'sources'
    elif 'metadata' in bucket_path:
        bq_table = 'temp_metadata'

    if not bq_table:
        print(f'No table given in {bucket_path}')

    job = bq_client.load_table_from_uri(
        f'gs://{bucket}/{bucket_path}',
        f'observations.{bq_table}',
    )

    job.result()
    print(f'Added {job.output_rows} to `observations.{bq_table}`')
