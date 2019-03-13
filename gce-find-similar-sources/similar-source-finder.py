import os
import time

from google.cloud import storage
from google.cloud import pubsub

import pandas as pd

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-observation-psc')
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

# Pubsub
PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'gce-find-similar-sources')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'


def main():
    print(f"Starting similar source finder on {pubsub_sub_path}")

    try:
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            pubsub_sub_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        print(f"Similar source finder subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        print(f'Problem starting subscriber: {e!r}')
        future.cancel()


def msg_callback(message):

    attributes = message.attributes
    sequence_id = attributes['sequence_id']

    bucket_path = f'{sequence_id}.csv'
    sources_bucket_path = f'{sequence_id}-similar-sources.csv'

    try:
        print(f'Fetching {bucket_path}')
        local_fn = download_blob(bucket_path, destination='/tmp', bucket=bucket)

        similar_sources = find_similar_sources(local_fn)

        local_sources_fn = f'{sequence_id}-similar-sources.csv'.replace('/', '_')
        local_sources_fn = os.path.join('/tmp', local_sources_fn)
        print(f'Making {local_sources_fn}')
        similar_sources.to_csv(local_sources_fn)

        upload_blob(local_sources_fn, sources_bucket_path, bucket=bucket)
    finally:
        print(f'Finished processing {sequence_id}.')
        message.ack()


def find_similar_sources(sources_fn):
    print(f'Loading PSC CSV for {sources_fn}')
    stamps_df = pd.read_csv(sources_fn, parse_dates=True).set_index(['image_time', 'picid'])

    # Normalize each stamp
    print(f'Normalizing PSC for {sources_fn}')
    norm_df = stamps_df.copy().apply(lambda x: x / stamps_df.sum(axis=1))

    top_matches = dict()
    print(f'Starting loop of PSCs for {sources_fn}')
    for picid, row in norm_df.groupby('picid'):
        norm_target = row.droplevel('picid')
        norm_group = ((norm_df - norm_target)**2).dropna().sum(axis=1).groupby('picid')
        top_matches[picid] = norm_group.sum().sort_values()

    print(f'Making DataFrame of similar sources for {sources_fn}')
    similar_sources = pd.DataFrame(top_matches)

    return similar_sources


def download_blob(source_blob_name, destination=None, bucket=None, bucket_name='panoptes-survey'):
    """Downloads a blob from the bucket."""
    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(source_blob_name)

    # If no name then place in current directory
    if destination is None:
        destination = source_blob_name.replace('/', '_')

    if os.path.isdir(destination):
        destination = os.path.join(destination, source_blob_name.replace('/', '_'))

    blob.download_to_filename(destination)

    print('Blob {} downloaded to {}.'.format(source_blob_name, destination))

    return destination


def upload_blob(source_file_name, destination, bucket=None, bucket_name='panoptes-survey'):
    """Uploads a file to the bucket."""
    print('Uploading {} to {}.'.format(source_file_name, destination))

    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination))


if __name__ == '__main__':
    main()
