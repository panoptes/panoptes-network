import os
import sys
import tempfile
import concurrent.futures
import time

import numpy as np
import pandas as pd

from google.cloud import firestore
from google.cloud import pubsub
from google.cloud import pubsub_v1
from google.cloud import storage
from google.cloud import bigquery

from astropy.io import fits

from panoptes.utils import sources
from panoptes.utils import image_id_from_path
from panoptes.utils import sequence_id_from_path
from panoptes.utils.images import fits as fits_utils
from panoptes.utils.images import bayer
from panoptes.utils.logger import logger

logger.enable('panoptes')
logger.remove()
logger.add(sys.stderr, format='{message}')

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
PUBSUB_SUBSCRIPTION = 'plate-solve-read'
INCOMING_BUCKET = os.getenv('INCOMING_BUCKET_NAME', 'panoptes-incoming')
OBSERVATIONS_BUCKET = os.getenv('OBSERVATIONS_BUCKET_NAME', 'panoptes-observations')
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 10)

# Storage
try:
    bq_client = bigquery.Client()
    firestore_db = firestore.Client()
    storage_client = storage.Client()
    incoming_bucket = storage_client.get_bucket(INCOMING_BUCKET)
    observations_bucket = storage_client.get_bucket(OBSERVATIONS_BUCKET)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


def main():
    """Continuously pull messages from subscription"""
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, PUBSUB_SUBSCRIPTION)

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
            streaming_pull_future.close()
            print(f'Streaming pull cancelled: {e!r}')
        finally:
            print(f'Streaming pull finished')


def process_message(message):
    """Receives the message and process necessary steps.

    Args:
        message (dict): The PubSub message. Data is delivered as attributes to
            the message. Valid keys are `bucket_path` (required) and `step`
            (optional, defaults to 'solve'). The `step` is the requested
            step and must be greater than the current status of the image document.
    """
    print(f"message received: {message!r}")

    bucket_path = message.pop('bucket_path')
    timeout = message.get('timeout', 600)  # 10 min timeout

    # Start separate process with message message.
    with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
        t0 = time.time()
        try:
            args = (bucket_path,)
            # Submit the function for execution.
            future = executor.submit(solve_file, *args, **message)
            # Wait for function to finish.
            future.result(timeout=timeout)
        except Exception as e:
            print(f'Error in {bucket_path} plate solve: {e!r}')
            image_id = image_id_from_path(bucket_path)
            firestore_db.document(f'images/{image_id}').set(dict(status='error'), merge=True)
        finally:
            t1 = time.time()
            print(f'{bucket_path} plate solve ran in {round(t1 - t0, 4)}')


def download_file(tmp_dir_name, bucket_path):
    fits_blob = incoming_bucket.get_blob(bucket_path)
    if not fits_blob:
        raise FileNotFoundError(f"Can't find {bucket_path} in {INCOMING_BUCKET}")

    # Download file
    print(f'Downloading image for {bucket_path}.')
    local_path = os.path.join(tmp_dir_name, bucket_path.replace('/', '-'))
    with open(local_path, 'wb') as f:
        fits_blob.download_to_file(f)

    return local_path


def solve_file(bucket_path, solve_config=None, background_config=None):
    """Plate solves the file after performing simple background subtraction.

    Notes:
        The background subtraction is not meant to be robust be we do record the
        statistics just to track in a simple way how it is changing over the course
        of an observation.

    Args:
        bucket_path (str): The relative path to the file blob.
        solve_config (dict|None): An optional dictionary of plate-solve configuration items.
        background_config (dict|None): An optional dictionary of plate-solve configuration items.

    """
    tmp_dir_name = tempfile.TemporaryDirectory()
    print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')

    # Extract the sequence_id and image_id from the path directly.
    # Note that this helps with some legacy units where the unit_id
    # was given a friendly name, which then propagated into the sequence_id
    # and image_id. This could potentially be removed in future although
    # the path, sequence_id, and image_id should always match so should
    # be okay to leave. wtgee 04-20
    image_id = image_id_from_path(bucket_path)
    sequence_id = sequence_id_from_path(bucket_path)
    print(f'Solving sequence_id={sequence_id} image_id={image_id} for {bucket_path}')

    image_doc_ref = firestore_db.document(f'images/{image_id}')
    image_solved = image_doc_ref.get(['solved']).get('solved', False)

    if image_solved:
        print(f'Image has been solved, skipping.')
        return

    # Blob for solved image.
    incoming_blob = incoming_bucket.blob(bucket_path)

    # Download image from storage bucket.
    local_path = download_file(tmp_dir_name, bucket_path)

    if solve_config is None:
        solve_config = {
            "skip_solved": False,
            "timeout": 120
        }
    if background_config is None:
        background_config = {
            "camera_bias": 2048.,
            "filter_size": 3,
            "box_size": (84, 84),
        }
    print(f"Starting plate-solving for FITS file {bucket_path}")

    data = fits_utils.getdata(local_path)
    header = fits_utils.getheader(local_path)

    header.update(dict(FILENAME=incoming_blob.public_url, SEQID=sequence_id, IMAGEID=image_id))
    bg_header = header.copy()

    subtracted_data = data
    # Get the background and store some stats about it.
    percentiles = [10, 25, 50, 75, 90]
    background_info = dict(background_median=dict(), background_rms=dict())
    try:
        rgb_backs = bayer.get_rgb_background(local_path,
                                             return_separate=True,
                                             **background_config)
        if len(rgb_backs) is None:
            print(f'Could not get RGB background for {local_path}, plate-solving without')
            header['BACKFAIL'] = True
        else:
            print(f'Got background for {local_path}')
            # Create one array for the backgrounds, where any holes are filled with zeros.
            rgb_masks = bayer.get_rgb_masks(fits_utils.getdata(local_path))
            full_background = np.array([np.ma.array(data=d0.background, mask=m0).filled(0)
                                        for d0, m0
                                        in zip(rgb_backs, rgb_masks)]).sum(0)

            # Get the actual background subtracted data.
            subtracted_data = (data - full_background).copy()

            # Save background file as unsigned int16.
            bg_header['COMMENT'] = "RGB background. The first three extensions (after the primary)"
            bg_header['COMMENT'] = "are for RGB background maps, the next three are the RMS maps."

            empty_primary_hdu = fits.PrimaryHDU(header=bg_header)
            hdu_list = fits.HDUList([empty_primary_hdu])

            for color, back_data in zip('rgb', rgb_backs):
                print(f'Creating {color} background file for {bucket_path}')
                back_hdu = fits.ImageHDU(data=back_data.background.astype(np.uint16))
                rms_hdu = fits.ImageHDU(data=back_data.background_rms.astype(np.uint16))

                hdu_list.extend([back_hdu, rms_hdu])

                # Info to save to firestore.
                background_info['background_median'][color] = np.percentile(
                    back_data.background,
                    q=percentiles
                )
                background_info['background_rms'][color] = np.percentile(
                    back_data.background_rms,
                    q=percentiles
                )

            back_path = local_path.replace('.fits', f'-background.fits')
            back_path = back_path.replace('.fz', '')  # Remove fz if present.

            # Save and compress the background file.
            hdu_list.writeto(back_path, overwrite=True)
            back_path = fits_utils.fpack(back_path)

            # Save the background alongside the normal image.
            back_bucket_name = bucket_path.replace('.fits', f'-background.fits')
            blob = observations_bucket.blob(back_bucket_name)
            print(f'Uploading background file for {back_path} to {blob.public_url}')
            blob.upload_from_filename(back_path)
    except Exception as e:
        print(f'Problem getting background for {local_path}: {e!r}')

    # Save subtracted file locally for solving.
    print(f'Creating new background subtracted file for {local_path}')
    primary_image_hdu = fits.PrimaryHDU(data=subtracted_data, header=header)

    primary_image_path = local_path.replace('.fits', '-back-sub.fits')
    primary_image_path = primary_image_path.replace('.fz', '')
    primary_image_hdu.writeto(primary_image_path, overwrite=True)
    assert os.path.exists(primary_image_path)

    print(f'Plate solving background subtracted {primary_image_path} with args: {solve_config!r}')
    solve_info = fits_utils.get_solve_field(primary_image_path, **solve_config)
    solved_path = solve_info['solved_fits_file'].replace('.new', '.fits')

    # Save over original file with new headers but old data.
    print(f'Creating new plate-solved file for {local_path} from {solved_path}')
    solved_header = fits_utils.getheader(solved_path)
    # Remove old astrometry.net comments.
    solved_header.remove('COMMENT', ignore_missing=True, remove_all=True)
    solved_header['STATUS'] = 'solved'

    solved_hdu = fits.PrimaryHDU(data=data.astype(np.uint16), header=solved_header)
    solved_hdu.writeto(solved_path, overwrite=True)
    solved_path = fits_utils.fpack(solved_path)

    outgoing_blob = observations_bucket.blob(bucket_path)
    print(f'Uploading {solved_path} to {outgoing_blob.public_url}')
    outgoing_blob.upload_from_filename(solved_path)

    image_doc_updates = dict(
        status='solved',
        solved=True,
        public_url=outgoing_blob.public_url,
        ra_image=solved_header.get('CRVAL1'),
        dec_image=solved_header.get('CRVAL2')
    )

    # Record the metadata in firestore.
    batch = firestore_db.batch()
    batch.set(
        image_doc_ref,
        image_doc_updates,
        merge=True
    )
    batch.commit()


if __name__ == '__main__':
    main()
