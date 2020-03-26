import os
import sys
import tempfile
import time

from google.cloud import firestore
from google.cloud import storage
from google.cloud import pubsub

from astropy.io import fits

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.images.bayer import get_rgb_background
from panoptes.utils import image_id_from_path
from panoptes.utils.serializers import from_json


try:
    db = firestore.Client()
except Exception as e:
    print(f'Error getting firestore client: {e!r}')

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
PUBSUB_SUBSCRIPTION = 'plate-solve-read'

# Storage
try:
    storage_client = storage.Client()
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 1)


def main():
    """Continuously pull messages from subsciption"""
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, PUBSUB_SUBSCRIPTION)

    print('Starting the Pubsub listen loop.')
    while True:
        try:
            response = subscriber.pull(subscription_path,
                                       max_messages=MAX_MESSAGES,
                                       timeout=30)
        except Exception as e:
            print(f"Can't pull messages: {e!r}")
            time.sleep(30)
            continue

        # If nothing found, sleep for 10 minutes.
        if len(response.received_messages) == 0:
            print(f'No plate solve requests found. Sleeping for 10 minutes.')
            time.sleep(600)

        ack_ids = list()
        for msg in response.received_messages:
            print(f"Received message: {msg.message}")

            # Process
            try:
                data = from_json(msg.message.data.decode())
                print(f"Data received: {data!r}")
                process_topic(data)
            except Exception as e:
                print(f'Problem plate-solving message: {e!r}')
            finally:
                print(f'Adding ack_id={msg.ack_id}')
                ack_ids.append(msg.ack_id)

        if ack_ids:
            print(f'Ack IDS: {ack_ids}')
            try:
                subscriber.acknowledge(subscription_path, ack_ids)
            except Exception as e:
                print(f'Problem acknowledging messages: {e!r}')


def process_topic(data):
    """Plate-solve a FITS file.

    Returns:
        TYPE: Description
    """
    bucket_name = data.get('bucket_name', BUCKET_NAME)
    bucket_path = data.get('bucket_path', None)
    solve_config = data.get('solve_config', {
        "skip_solved": False,
        "timeout": 120
    })
    background_config = data.get('background_config', {
        "camera_bias": 2048.,
        "filter_size": 20,
    })
    print(f"Staring plate-solving for FITS file {bucket_path}")
    if bucket_path is not None:

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
            bucket = storage_client.get_bucket(bucket_name)
            try:
                print(f'Getting blob for {bucket_path}.')
                fits_blob = bucket.get_blob(bucket_path)
                if not fits_blob:
                    raise FileNotFoundError(f"Can't find {bucket_path} in {bucket_name}")

                image_id = image_id_from_path(bucket_path)
                print(f'Got image_id {image_id} for {bucket_path}')

                # Get the metadata from firestore.
                image_doc_ref = db.document(f'images/{image_id}')
                image_doc = image_doc_ref.get().to_dict() or dict()
                if image_doc.get('solved', False):
                    print(f'Image has been solved by plate-solver {image_id}, skipping solve')

                # Download file
                print(f'Downloading image for {bucket_path}.')
                local_path = os.path.join(tmp_dir_name, bucket_path.replace('/', '-'))
                with open(local_path, 'wb') as f:
                    fits_blob.download_to_file(f)

                # Do the actual plate-solve.
                solved_path = solve_file(local_path, background_config, solve_config)
                print(f'Done solving, new path: {solved_path}')

                # Compress if needed.
                if not solved_path.endswith('.fz'):
                    print(f'Compressing: {solved_path}')
                    solved_path = fits_utils.fpack(solved_path)
                    bucket_path = bucket_path.replace('.fits', '.fits.fz')
                    fits_blob = bucket.rename_blob(fits_blob, bucket_path)

                # Replace file on bucket with solved file.
                print(f'Uploading {solved_path} to {fits_blob.path}')
                fits_blob.upload_from_filename(solved_path)

                # Update firestore record.
                image_doc_ref.set(dict(status='solved', solved=True, bucket_path=bucket_path), merge=True)

            except Exception as e:
                print(f'Problem with plate solving file: {e!r}')
                if image_doc_ref:
                    image_doc_ref.set(dict(status='solve_error'), merge=True)
            finally:
                print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')


def solve_file(local_path, background_config, solve_config):
    print(f'Entering solve_file for {local_path}')
    solved_file = None

    # Get the background subtracted data.
    header = fits_utils.getheader(local_path)
    data = fits_utils.getdata(local_path)

    try:
        observation_background = get_rgb_background(local_path, **background_config)
        if observation_background is None:
            print(f'Could not get RGB background for {local_path}, plate-solving without')
            header['BACKFAIL'] = True
            data = data - observation_background
        else:
            print(f'Got background for {local_path}')
    except Exception as e:
        print(f'Problem getting background for {local_path}: {e!r}')

    print(f'Creating new background subtracted file for {local_path}')
    # Save subtracted file locally.
    hdu = fits.PrimaryHDU(data=data, header=header)

    back_path = local_path.replace('.fits', '-background.fits')
    back_path = local_path.replace('.fz', '')
    hdu.writeto(back_path, overwrite=True)
    assert os.path.exists(back_path)

    print(f'Plate solving background subtracted {back_path} with args: {solve_config!r}')
    solve_info = fits_utils.get_solve_field(back_path, **solve_config)
    solved_file = solve_info['solved_fits_file'].replace('.new', '.fits')

    # Save over original file with new headers but old data.
    print(f'Creating new plate-solved file for {local_path}')
    solved_header = fits_utils.getheader(solved_file)
    solved_header['status'] = 'solved'
    hdu = fits.PrimaryHDU(data=data, header=solved_header)
    hdu.writeto(local_path, overwrite=True)

    return local_path


if __name__ == '__main__':
    main()
