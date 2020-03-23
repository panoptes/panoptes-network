import os
import sys
import json

from google.cloud import pubsub
from google.cloud import firestore

try:
    db = firestore.Client()
except Exception as e:
    print(f'Error getting firestore client: {e!r}')

publisher = pubsub.PublisherClient()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'panoptes-exp')
pubsub_base = f'projects/{project_id}/topics'

plate_solve_topic = os.getenv('SOLVER_topic', 'plate-solve')
fits_packer_topic = os.getenv('FPACK_topic', 'compress-fits')
make_rgb_topic = os.getenv('RGB_topic', 'make-rgb-fits')


def entry_point(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.

    This will send a pubsub message to a certain topic depending on
    what type of file was uploaded. The servies responsible for those
    topis do all the processing.

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    try:
        print(f"Received: {data!r}")
        process_topic(data)
        # Flush the stdout to avoid log buffering.
        sys.stdout.flush()

    except Exception as e:
        print(f'error: {e}')


def process_topic(data):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket.

    FITS: Set header variables and then forward to endpoint for adding headers
    to the metadatabase. The header is looked up from the file id, including the
    storage bucket file generation id, which are stored into the headers.

    CR2: Trigger creation of timelapse and jpg images.

    Example file id:

    panoptes-raw-images/PAN001/14d3bd/20181011T134202/20181011T134333.fits.fz

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    bucket_path = data['name']

    if bucket_path is None:
        raise Exception(f'No file requested')

    _, file_ext = os.path.splitext(bucket_path)

    process_lookup = {
        '.fits': process_fits,
        '.fz': process_fits,
        '.cr2': process_cr2,
    }

    print(f"Processing {bucket_path}")

    try:
        process_lookup[file_ext](bucket_path)
    except KeyError:
        raise Exception(f'No handling for {file_ext}')


def send_pubsub_message(topic, data):
    print(f"Sending message to {topic}: {data!r}")
    data = json.dumps(data).encode()

    def callback(future):
        message_id = future.result()
        print(f'Pubsub message to {topic} received: {message_id}')

    publisher.publish(f'{pubsub_base}/{topic}', data)


def process_fits(bucket_path):
    send_pubsub_message(plate_solve_topic, dict(bucket_path=bucket_path))


def process_cr2(bucket_path):
    send_pubsub_message(make_rgb_topic, dict(bucket_path=bucket_path))
