import os
import sys
import tempfile
import time
from contextlib import suppress
from dateutil.parser import parse as parse_date
from collections import defaultdict
import numpy as np

from google.cloud import firestore
from google.cloud import storage
from google.cloud import pubsub

from astropy.io import fits

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.images.bayer import get_rgb_background
from panoptes.utils import image_id_from_path
from panoptes.utils.serializers import from_json
from panoptes.utils.logger import logger

logger.enable('panoptes')
logger.remove()
logger.add(sys.stderr, format='{message}')

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
BACKGROUND_BUCKET_NAME = os.getenv('BACKGROUND_BUCKET_NAME', 'panoptes-backgrounds')
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
            # print(f'No plate solve requests found. Sleeping for 10 minutes.')
            time.sleep(60)

        ack_ids = list()
        for msg in response.received_messages:
            print(f"Received message: {msg.message}")

            # Process
            try:
                data = from_json(msg.message.data.decode())
                print(f"Data received: {data!r}")

                # Get image info.
                bucket_path = data.get('bucket_path')
                image_id = image_id_from_path(bucket_path)
                print(f'Got image_id {image_id} for {bucket_path}')

                image_doc_ref = db.document(f'images/{image_id}')
                image_doc_snap = image_doc_ref.get()
                print(f'Record in firetore: {image_doc_snap.exists}')

                # Skip image if previously solved.
                image_doc = image_doc_snap.to_dict() or dict()
                if image_doc.get('solved', False) or image_doc.get('status') == 'solved':
                    print(f'Image has been solved by plate-solver {image_id}, skipping solve')
                    break

                # Send to solver processing.
                process_topic(image_doc_ref, data)

            except Exception as e:
                print(f'Problem plate-solving message: {e!r}')
                if image_doc_ref:
                    image_doc_ref.set(dict(status='solve_error', solved=False), merge=True)
            finally:
                print(f'Adding ack_id={msg.ack_id}')
                ack_ids.append(msg.ack_id)

        if ack_ids:
            print(f'Ack IDS: {ack_ids}')
            try:
                subscriber.acknowledge(subscription_path, ack_ids)
            except Exception as e:
                print(f'Problem acknowledging messages: {e!r}')


def process_topic(image_doc_ref, data):
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

                # Download file
                print(f'Downloading image for {bucket_path}.')
                local_path = os.path.join(tmp_dir_name, bucket_path.replace('/', '-'))
                with open(local_path, 'wb') as f:
                    fits_blob.download_to_file(f)

                headers = {'FILENAME': fits_blob.public_url}

                # Do the actual plate-solve.
                print(f'Calling solve_field for {local_path} from {bucket_path}.')
                solved_path = solve_file(local_path,
                                         background_config,
                                         solve_config,
                                         headers,
                                         image_doc_ref,
                                         bucket_path)
                print(f'Done solving, new path: {solved_path} for {bucket_path}')

                if not bucket_path.endswith('.fz'):
                    print(f'Renaming {bucket_path} to {bucket_path}.fz because we compressed')
                    fits_blob = bucket.rename_blob(fits_blob, f'{bucket_path}.fz')

                # Replace file on bucket with solved file.
                print(f'Uploading {solved_path} for {bucket_path}')
                fits_blob.upload_from_filename(solved_path)

                print(f'Adding metadata record to firestore for {solved_path}')
                headers = fits_utils.getheader(solved_path)
                add_header_to_db(image_doc_ref, headers)

            except Exception as e:
                print(f'Problem with plate solving file: {e!r}')
            finally:
                print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')


def solve_file(local_path, background_config, solve_config, headers, image_doc_ref, bucket_path):
    print(f'Entering solve_file for {local_path}')
    solved_file = None

    # Get the background subtracted data.
    header = fits_utils.getheader(local_path)
    header.update(headers)
    data = fits_utils.getdata(local_path)

    try:
        observation_background = get_rgb_background(local_path,
                                                    return_separate=True,
                                                    **background_config)
        if len(observation_background) is None:
            print(f'Could not get RGB background for {local_path}, plate-solving without')
            header['BACKFAIL'] = True
        else:
            print(f'Got background for {local_path}')
            # Create one array for the backgrounds, where any holes are filled with zeros.
            full_background = np.ma.array(observation_background).sum(0).filled(0)
            data = data - full_background

            back_bucket = storage_client.get_bucket(BACKGROUND_BUCKET_NAME)
            background_info = defaultdict(dict)

            for color, back_data in zip('rgb', observation_background):
                background_info['background_median'][color] = np.ma.median(back_data)
                background_info['background_rms'][color] = np.ma.std(back_data)

                # Save background file.
                hdu = fits.PrimaryHDU(data=back_data.data, header=header)

                back_path = local_path.replace('.fits', f'-background-{color}.fits')
                back_path = back_path.replace('.fz', '')
                print(f'Creating background file for {back_path}')
                hdu.writeto(back_path, overwrite=True)
                back_path = fits_utils.fpack(back_path)

                blob = back_bucket.blob(bucket_path.replace('.fits', f'-background-{color}.fits'))
                print(f'Uploading background file for {back_path} to {blob.public_url}')
                blob.upload_from_filename(back_path)

            # Record background details in image.
            image_doc_ref.set(background_info, merge=True)
    except Exception as e:
        print(f'Problem getting background for {local_path}: {e!r}')

    print(f'Creating new background subtracted file for {local_path}')
    # Save subtracted file locally.
    hdu = fits.PrimaryHDU(data=data, header=header)

    back_path = local_path.replace('.fits', '-back-sub.fits')
    back_path = local_path.replace('.fz', '')
    hdu.writeto(back_path, overwrite=True)
    assert os.path.exists(back_path)

    print(f'Plate solving background subtracted {back_path} with args: {solve_config!r}')
    solve_info = fits_utils.get_solve_field(back_path, **solve_config)
    solved_file = solve_info['solved_fits_file'].replace('.new', '.fits')

    # Save over original file with new headers but old data.
    print(f'Creating new plate-solved file for {local_path} from {solved_file}')
    solved_header = fits_utils.getheader(solved_file)
    solved_header['status'] = 'solved'
    hdu = fits.PrimaryHDU(data=data, header=solved_header)

    overwrite_local_path = local_path.replace('.fz', '')
    hdu.writeto(overwrite_local_path, overwrite=True)

    print(f'Compressing: {overwrite_local_path}')
    overwrite_local_path = fits_utils.fpack(overwrite_local_path)

    return overwrite_local_path


def add_header_to_db(image_doc_ref, header):
    """Add FITS image info to metadb.

    Note:
        This function doesn't check header for proper entries and
        assumes a large list of keywords. See source for details.

    Args:
        header (dict): FITS Header data from an observation.
        bucket_path (str): Full path to the image in a Google Storage Bucket.

    Returns:
        str: The image_id.

    Raises:
        e: Description
    """
    bucket_path = header.get('FILENAME')
    print(f'Cleaning headers for {bucket_path}')
    header.remove('COMMENT', ignore_missing=True, remove_all=True)
    header.remove('HISTORY', ignore_missing=True, remove_all=True)

    # Scrub all the entries
    for k, v in header.items():
        with suppress(AttributeError):
            header[k] = v.strip()

    # print(f'Using headers: {header!r}')
    try:
        seq_id = header.get('SEQID', '')

        unit_id, camera_id, sequence_time = seq_id.split('_')
        sequence_time = parse_date(sequence_time)

        image_id = header.get('IMAGEID', '')
        img_time = parse_date(image_id.split('_')[-1])

        print(f'Getting document for observation {seq_id}')
        seq_doc_ref = db.document(f'observations/{seq_id}')
        seq_doc_snap = seq_doc_ref.get()

        # Only process sequence if in a certain state.
        valid_status = ['metadata_received', 'solve_error', 'uploaded', 'receiving_files']

        if not seq_doc_snap.exists or seq_doc_snap.get('status') in valid_status:
            print(f'Making new document for observation {seq_id}')
            # If no sequence doc then probably no unit id. This is just to minimize
            # the number of lookups that would be required if we looked up unit_id
            # doc each time.
            print(f'Getting doc for unit {unit_id}')
            unit_doc_ref = db.document(f'units/{unit_id}')
            unit_doc_snap = unit_doc_ref.get()

            # Add a units doc if it doesn't exist.
            if not unit_doc_snap.exists:
                try:
                    unit_data = {
                        'name': header.get('OBSERVER', ''),
                        'location': firestore.GeoPoint(header['LAT-OBS'], header['LONG-OBS']),
                        'elevation': float(header.get('ELEV-OBS')),
                        'status': 'active'  # Assuming we are active since we received files.
                    }
                    unit_doc_ref.set(unit_data, merge=True)
                except Exception:
                    pass

            seq_data = {
                'unit_id': unit_id,
                'camera_id': camera_id,
                'time': sequence_time,
                'exptime': header.get('EXPTIME'),
                'project': header.get('ORIGIN'),  # Project PANOPTES
                'software_version': header.get('CREATOR', ''),
                'field_name': header.get('FIELD', ''),
                'iso': header.get('ISO'),
                'ra': header.get('CRVAL1'),
                'dec': header.get('CRVAL2'),
                'status': 'receiving_files',
            }

            try:
                print("Inserting sequence: {}".format(seq_data))
                seq_doc_ref.set(seq_data, merge=True)
            except Exception as e:
                print(f"Can't insert sequence {seq_id}: {e!r}")

        image_doc_snap = image_doc_ref.get()
        image_status = image_doc_snap.get('status')

        if not image_doc_snap.exists or image_status in valid_status:
            print(f"Adding image document for SEQ={seq_id} IMG={image_id}")

            image_data = {
                'sequence_id': seq_id,
                'time': img_time,
                'bucket_path': bucket_path,
                'status': 'solved',
                'solved': True,
                'airmass': header.get('AIRMASS'),
                'exptime': header.get('EXPTIME'),
                'moonfrac': header.get('MOONFRAC'),
                'moonsep': header.get('MOONSEP'),
                'ra_image': header.get('CRVAL1'),
                'dec_image': header.get('CRVAL2'),
                'ha_mnt': header.get('HA-MNT'),
                'ra_mnt': header.get('RA-MNT'),
                'dec_mnt': header.get('DEC-MNT'),
            }
            try:
                image_doc_ref.set(image_data, merge=True)
            except Exception as e:
                print(f"Can't insert image info {image_id}: {e!r}")
        else:
            print(f'Image exists with status={image_status} so not updating record details')

    except Exception as e:
        raise e

    return True


if __name__ == '__main__':
    main()
