import os
import sys
import time
import subprocess

from google.cloud import firestore
from google.cloud import pubsub
from google.cloud import pubsub_v1
from google.cloud import storage

from panoptes.utils import image_id_from_path

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
PUBSUB_SUBSCRIPTION = 'plate-solve-read'
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 1)
INCOMING_BUCKET = os.getenv('INCOMING_BUCKET', 'panoptes-incoming')
ERROR_BUCKET = os.getenv('ERROR_BUCKET', 'panoptes-error-images')

# Storage
try:
    firestore_db = firestore.Client()
    """Continuously pull messages from subscription"""
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, PUBSUB_SUBSCRIPTION)

    storage_client = storage.Client()
    incoming_bucket = storage_client.get_bucket(INCOMING_BUCKET)
    error_bucket = storage_client.get_bucket(ERROR_BUCKET)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


def main():
    print(f'Creating subscriber (messages={MAX_MESSAGES}) for {subscription_path}')
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=process_message,
        flow_control=pubsub_v1.types.FlowControl(max_messages=int(MAX_MESSAGES))
    )

    print(f'Listening for messages on {subscription_path}')
    with subscriber:
        try:
            streaming_pull_future.result()  # Blocks indefinitely
        except Exception as e:
            streaming_pull_future.cancel()
            print(f'Streaming pull cancelled: {e!r}')
        finally:
            print(f'Streaming pull finished')


def process_message(message):
    """Receives the message and process necessary steps.

    Args:
        message (`google.cloud.pubsub.Message`): The PubSub message. Data is delivered
            as attributes to the message. Valid keys are `bucket_path` (required).
    """
    data = message.data.decode('utf-8')
    attributes = dict(message.attributes)

    try:
        bucket_path = attributes.pop('bucket_path')
    except KeyError:
        bucket_path = data['bucket_path']

    timeout = attributes.get('timeout', 600)  # 10 min timeout

    print(f"Message received: {message!r}")

    if bucket_path is None:
        print(f'Need a valid bucket_path')
        return

    image_id = image_id_from_path(bucket_path)
    processing_ref = firestore_db.document(f'processing/plate-solve')
    processing_ref.set(dict(image_ids=firestore.ArrayUnion([image_id])), merge=True)

    t0 = time.time()
    try:
        solve_cmd = ['/app/solver.py', '--bucket-path', bucket_path]
        print(f'Submitting {solve_cmd}')
        completed_process = subprocess.run(solve_cmd,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           check=True,
                                           timeout=timeout)
        print(f'Plate solve completed successfully for {bucket_path}')
        print(f'{bucket_path} solver output: {completed_process.stdout}')
    except subprocess.CalledProcessError as e:
        print(f'Error in {bucket_path} plate solve script: {e!r}')
        print(f'{bucket_path} solver stdout: {e.stdout}')
        print(f'{bucket_path} solver stderr: {e.stderr}')
        print(f'{bucket_path} solver output: {e.output}')
        firestore_db.document(f'images/{image_id}').set(dict(status='error'), merge=True)

        error_blob = incoming_bucket.copy_blob(incoming_bucket.blob(bucket_path), error_bucket)
        print(f'Moved error FITS {bucket_path} to {error_blob.public_url}')
    except Exception as e:
        print(f'Error in {bucket_path} plate solve: {e!r}')
        error_blob = incoming_bucket.copy_blob(incoming_bucket.blob(bucket_path), error_bucket)
        print(f'Moved error FITS {bucket_path} to {error_blob.public_url}')
    finally:
        t1 = time.time()
        print(f'{bucket_path} plate solve ran in {t1 - t0:0.2f} seconds')
        processing_ref.set(dict(image_ids=firestore.ArrayRemove([image_id])), merge=True)
        message.ack()


if __name__ == '__main__':
    main()
