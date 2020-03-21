import os
import sys
import json

from google.cloud import pubsub

publisher = pubsub.PublisherClient()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'panoptes-exp')
pubsub_base = f'projects/{project_id}/topics'

add_header_topic = os.getenv('HEADER_topic', 'record-image')
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
        '.fz': process_fz,
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


def process_fz(bucket_path):
    """ Forward the headers to the -add-header-to-db Cloud Function.

    Args:
        bucket_path (str): The relative (to the bucket) path of the file in the storage bucket.
    """
    # Get some of the fields from the path.
    unit_id, camera_id, seq_time, filename = bucket_path.split('/')

    # Get the image time from the filename
    image_time = filename.split('.')[0]

    # Build the sequence and image ids
    sequence_id = f'{unit_id}_{camera_id}_{seq_time}'
    image_id = f'{unit_id}_{camera_id}_{image_time}'

    headers = {
        'PANID': unit_id,
        'INSTRUME': camera_id,
        'SEQTIME': seq_time,
        'IMGTIME': image_time,
        'SEQID': sequence_id,
        'IMAGEID': image_id,
        'FILENAME': bucket_path,
        'PSTATE': 'fits_received'
    }

    # Send to add-header-to-db
    send_pubsub_message(add_header_topic, {
        'headers': headers,
        'bucket_path': bucket_path,
    })


def process_fits(bucket_path):
    """ Publish a message on the topic to trigger fits packing.

    Args:
        bucket_path (str): The relative (to the bucket) path of the file in the storage bucket.
    """
    send_pubsub_message(fits_packer_topic, dict(bucket_path=bucket_path))


def process_cr2(bucket_path):
    send_pubsub_message(make_rgb_topic, dict(cr2_file=bucket_path))


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=True)
