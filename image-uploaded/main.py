import os
import sys
import json

from google.cloud import pubsub
from google.cloud import storage
from google.cloud import firestore

from dateutil.parser import parse as date_parse

from panoptes.utils import image_id_from_path
from panoptes.utils import sequence_id_from_path


publisher = pubsub.PublisherClient()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'panoptes-exp')
pubsub_base = f'projects/{project_id}/topics'

plate_solve_topic = os.getenv('SOLVER_topic', 'plate-solve')
make_rgb_topic = os.getenv('RGB_topic', 'make-rgb-fits')

# Storage
storage_client = storage.Client()
storage_bucket = storage_client.get_bucket(os.getenv('BUCKET_NAME', 'panoptes-raw-images'))
timelapse_bucket = storage_client.get_bucket(os.getenv('TIMELAPSE_BUCKET_NAME', 'panoptes-timelapse'))
temp_bucket = storage_client.get_bucket(os.getenv('TEMP_BUCKET_NAME', 'panoptes-temp'))

firestore_db = firestore.Client()


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

    Triggered when file is uploaded to bucket and forwards on to appropriate service.

    This function first check to see if the file has the legacy field name in it,
    and if so rename the file (which will trigger this function again with new name).

    Correct:   PAN001/14d3bd/20200319T111240/20200319T112708.fits.fz
    Incorrect: PAN001/Tess_Sec21_Cam02/14d3bd/20200319T111240/20200319T112708.fits.fz

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
        '.jpg': lambda x: print(f'Saving {x}')
    }

    # Check if has legeacy path
    path_parts = bucket_path.split('/')
    if len(path_parts) == 5:
        field_name = path_parts.pop(1)
        new_path = '/'.join(path_parts)
        print(f'Removed field name ["{field_name}"]: {bucket_path} -> {new_path}')

        bucket = storage_bucket
        if file_ext == '.mp4':
            print(f'Timelapse. Moving {bucket_path} to timelapse bucket')
            bucket = timelapse_bucket
        elif file_ext not in list(process_lookup.keys()):
            print(f'Unknown extension. Moving {bucket_path} to temp bucket')
            bucket = temp_bucket

        bucket.rename_blob(storage_bucket.get_blob(bucket_path), new_path)

        return

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
    print(f'Recording {bucket_path} in firestore db.')
    add_records_to_db(bucket_path)
    send_pubsub_message(plate_solve_topic, dict(bucket_path=bucket_path))


def process_cr2(bucket_path):
    send_pubsub_message(make_rgb_topic, dict(bucket_path=bucket_path))


def add_records_to_db(bucket_path):
    image_id = image_id_from_path(bucket_path)
    sequence_id = sequence_id_from_path(bucket_path)

    unit_id, camera_id, sequence_time = sequence_id.split('_')
    image_time = image_id.split('_')[-1]

    # Make observation record
    seq_data = {
        'unit_id': unit_id,
        'camera_id': camera_id,
        'time': date_parse(sequence_time),
        'status': 'receiving_files',
        'processed_time': firestore.SERVER_TIMESTAMP,
        'num_images': firestore.Increment(1)
    }

    firestore_db.document(f'observations/{sequence_id}').set(seq_data, merge=True)

    # Make image record.
    image_data = {
        'sequence_id': sequence_id,
        'time': date_parse(image_time),
        'bucket_path': bucket_path,
        'status': 'received',
        'solved': False,
        'received_time': firestore.SERVER_TIMESTAMP
    }

    firestore_db.document(f'images/{image_id}').set(image_data, merge=True)
