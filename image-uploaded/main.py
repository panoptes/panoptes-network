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
    publisher.publish(f'{pubsub_base}/{topic}', json.dumps(data).encode())


def process_fits(bucket_path):
    try:
        add_records_to_db(bucket_path)
    except Exception as e:
        print(f'Error adding metadata for {bucket_path}: {e!r}')
    else:
        # Continue processing image if metadata insert successful.
        send_pubsub_message(plate_solve_topic, dict(bucket_path=bucket_path))


def process_cr2(bucket_path):
    send_pubsub_message(make_rgb_topic, dict(bucket_path=bucket_path))


def add_records_to_db(bucket_path):
    """Adds image informantion to firestore db.

    This function will first try to insert an `images` document for the file at
    the given `bucket_path`. If a record currently exists no further processing
    is done. If a new record is inserted, then this is the first time the image
    has been processed, so we also increment the corresponding `num_images`
    (and `modified_time`) fields in the corresponding `observations` document.

    Args:
        bucket_path (str): Path to file in bucket.
    """
    print(f'Recording {bucket_path} metadata.')
    image_id = image_id_from_path(bucket_path)
    sequence_id = sequence_id_from_path(bucket_path)

    unit_id, camera_id, sequence_time = sequence_id.split('_')
    image_time = image_id.split('_')[-1]

    # Make image document.
    image_data = {
        'sequence_id': sequence_id,
        'time': date_parse(image_time),
        'bucket_path': bucket_path,
        'status': 'uploaded',
        'solved': False,
        'received_time': firestore.SERVER_TIMESTAMP
    }
    # Upsert observation document
    seq_data = {
        'unit_id': unit_id,
        'camera_id': camera_id,
        'time': date_parse(sequence_time),
        'status': 'receiving_files',
        'modified_time': firestore.SERVER_TIMESTAMP,
        'num_images': firestore.Increment(1)
    }

    # Add the image document and upsert the observation document in transaction.
    batch = firestore_db.batch()
    batch.create(firestore_db.document(f'images/{image_id}'), image_data)
    batch.set(firestore_db.document(f'observations/{sequence_id}'), seq_data, merge=True)
    batch.commit()
