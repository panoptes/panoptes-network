import base64
import json
import sys

from google.cloud import bigquery

bq_client = bigquery.Client()


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

    bq_table = None
    if 'sources' in bucket_path:
        bq_table = 'sources'
    elif 'metadata' in bucket_path:
        bq_table = 'metadata'

    if not bq_table:
        print(f'No table given in {bucket_path}')

    dataset_id = 'observations'
    dataset_ref = bq_client.dataset(dataset_id)
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.PARQUET
    uri = f"gs://{bucket}/{bucket_path}"

    load_job = bq_client.load_table_from_uri(
        uri, dataset_ref.table(bq_table), job_config=job_config
    )
    print(f"Starting job {load_job.job_id}")

    # Blocking.
    load_job.result()
    print(f"Job finished loading {load_job.output_rows}")
