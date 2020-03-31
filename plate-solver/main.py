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
from google.cloud import bigquery

from astropy.io import fits

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.images import bayer
from panoptes.utils import image_id_from_path
from panoptes.utils import sequence_id_from_path
from panoptes.utils.serializers import from_json
from panoptes.utils.logger import logger
from panoptes.utils import sources

logger.enable('panoptes')
logger.remove()
logger.add(sys.stderr, format='{message}')

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
PUBSUB_SUBSCRIPTION = 'plate-solve-read'
RAW_BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')
PROCESSED_BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-processed-images')
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 1)

# Storage
try:
    db = firestore.Client()
    bq_client = bigquery.Client()
    storage_client = storage.Client()

    raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
    processed_bucket = storage_client.get_bucket(PROCESSED_BUCKET_NAME)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)


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
                process_topic(image_doc_snap, data)

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


def process_topic(image_doc_snap, data):
    """Plate-solve a FITS file.

    Returns:
        TYPE: Description
    """
    bucket_path = data.get('bucket_path', None)
    solve_config = data.get('solve_config', {
        "skip_solved": False,
        "timeout": 120
    })
    background_config = data.get('background_config', {
        "camera_bias": 2048.,
        "filter_size": 3,
        "box_size": (84, 84),
    })
    print(f"Staring plate-solving for FITS file {bucket_path}")
    if bucket_path is not None:

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
            try:
                print(f'Getting blob for {bucket_path}.')

                fits_blob = raw_bucket.get_blob(bucket_path)
                if not fits_blob:
                    raise FileNotFoundError(f"Can't find {bucket_path} in {RAW_BUCKET_NAME}")
                processed_blob = processed_bucket.blob(bucket_path)

                image_id = image_id_from_path(bucket_path)
                sequence_id = sequence_id_from_path(bucket_path)
                print(f'Got sequence_id={sequence_id} image_id={image_id} for {bucket_path}')

                # Download file
                print(f'Downloading image for {bucket_path}.')
                local_path = os.path.join(tmp_dir_name, bucket_path.replace('/', '-'))
                with open(local_path, 'wb') as f:
                    fits_blob.download_to_file(f)

                # Extract the sequence_id and image_id from the path directly.
                # Note that this helps with some legacy units where the unit_id
                # was given a friendly name, which then propogated into the sequence_id
                # and image_id. This could potentially be removed in future although
                # the path, sequence_id, and image_id should always match so should
                # be okay to leave. wtgee 04-20

                headers = {
                    'FILENAME': processed_blob.public_url,
                    'SEQID': sequence_id,
                    'IMAGEID': image_id,
                }

                # Do the actual plate-solve.
                print(f'Calling solve_field for {local_path} from {bucket_path}.')
                solved_path = solve_file(local_path,
                                         background_config,
                                         solve_config,
                                         headers,
                                         image_doc_snap,
                                         bucket_path)
                print(f'Done solving, new path: {solved_path} for {bucket_path}')

                # Replace file on bucket with solved file.
                print(f'Uploading {solved_path} to {processed_blob.public_url}')
                processed_blob.upload_from_filename(solved_path)

                print(f'Adding metadata record to firestore for {solved_path}')
                headers = fits_utils.getheader(solved_path)
                add_header_to_db(image_doc_snap, headers)

                # Source extraction.
                source_extraction(headers, solved_path, bucket_path, image_id, sequence_id)

            except Exception as e:
                print(f'Problem with plate solving file: {e!r}')
            finally:
                print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')


def source_extraction(headers, solved_path, bucket_path, image_id, sequence_id):
    print(f'Doing source extraction for {solved_path}')
    point_sources = sources.lookup_point_sources(solved_path,
                                                 catalog_match=True,
                                                 bq_client=bq_client)

    # Rename all columns to be from sextractor, then revert some.
    point_sources.rename(columns={c: f'sextractor_{c}'
                                  for c
                                  in point_sources.columns},
                         inplace=True,
                         errors='ignore')

    # Revert some of those from above.
    point_sources.rename(columns={
        'sextractor_picid': 'picid',
        'sextractor_vmag': 'catalog_vmag',
        'sextractor_vmag_err': 'catalog_vmag_err',
    },
        inplace=True,
        errors='ignore')

    # Add some of the FITS headers
    point_sources['exptime'] = headers['EXPTIME']

    point_sources['camera_iso'] = headers['ISO']
    point_sources['camera_temp'] = headers['CAMTEMP'].split(' ')[0]  # '16 C'
    point_sources['camera_circconf'] = headers['CIRCCONF'].split(' ')[0]  # '0.019 mm'
    point_sources['camera_colortmp'] = headers['COLORTMP']
    point_sources['camera_measev'] = headers['MEASEV']
    point_sources['camera_measev2'] = headers['MEASEV2']

    meas_r, meas_g1, meas_g2, meas_b = headers['MEASRGGB'].split(' ')  # = '455 1024 1024 784'
    point_sources['camera_meas_r'] = meas_r
    point_sources['camera_meas_g1'] = meas_g1
    point_sources['camera_meas_g2'] = meas_g2
    point_sources['camera_meas_b'] = meas_b

    point_sources['camera_whtlvln'] = headers['WHTLVLN']
    point_sources['camera_whtlvls'] = headers['WHTLVLS']
    point_sources['camera_redbal'] = headers['REDBAL']
    point_sources['camera_bluebal'] = headers['BLUEBAL']

    point_sources['mnt_ra'] = headers['RA-MNT']
    point_sources['mnt_ha'] = headers['HA-MNT']
    point_sources['mnt_dec'] = headers['DEC-MNT']
    point_sources['mnt_airmass'] = headers['AIRMASS']

    point_sources['location_lat'] = headers['LAT-OBS']
    point_sources['location_long'] = headers['LONG-OBS']
    point_sources['location_elev'] = headers['ELEV-OBS']

    point_sources['image_center_ra'] = headers['CRVAL1']
    point_sources['image_center_dec'] = headers['CRVAL2']

    unit_id, camera_id, image_time = image_id.split('_')
    seq_time = sequence_id.split('_')[-1]

    # Adjust some of the header items
    point_sources['image_id'] = image_id
    point_sources['image_time'] = image_time
    point_sources['sequence_time'] = seq_time
    point_sources['camera_id'] = camera_id
    point_sources['unit_id'] = unit_id

    sources_path = solved_path.replace('.fits.fz', '.csv.gz')

    print(f'Saving sources to {sources_path}')
    # Reorder the columns.
    point_sources.reindex(sorted(point_sources.columns), axis=1).to_csv(sources_path, index=False)

    sources_bucket_path = bucket_path.replace('.fits.fz', '.csv')
    sources_bucket_path = sources_bucket_path.replace('.fits', '.csv')  # Can be just a 'fits'

    sources_bucket_path = sources_bucket_path.replace('.csv', '-sources.csv.gz')
    sources_blob = processed_bucket.blob(sources_bucket_path)
    sources_blob.upload_from_filename(sources_path)
    print(f'{sources_path} uploaded to {sources_blob.public_url}')


def solve_file(local_path, background_config, solve_config, headers, image_doc_snap, bucket_path):
    print(f'Entering solve_file for {local_path}')
    solved_file = None

    # Get the background subtracted data.
    header = fits_utils.getheader(local_path)
    header.update(headers)
    data = fits_utils.getdata(local_path)

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
            subtracted_data = data - full_background

            back_bucket = storage_client.get_bucket(PROCESSED_BUCKET_NAME)
            background_info = defaultdict(lambda: defaultdict(dict))

            for color, back_data in zip('rgb', rgb_backs):
                # Save background file as unsigned int16
                back_hdu = fits.PrimaryHDU(data=back_data.background.astype(np.uint16),
                                           header=header)
                rms_hdu = fits.ImageHDU(data=back_data.background_rms.astype(np.uint16))

                back_path = local_path.replace('.fits', f'-background-{color}.fits')
                back_path = back_path.replace('.fz', '')
                print(f'Creating background file for {back_path}')
                hdul = fits.HDUList([back_hdu, rms_hdu])
                hdul.writeto(back_path, overwrite=True)

                back_path = fits_utils.fpack(back_path)

                back_bucket_name = bucket_path.replace('.fits', f'-background-{color}.fits')
                # back_bucket_name = back_bucket_name.replace('.fz', '')
                blob = back_bucket.blob(back_bucket_name)
                print(f'Uploading background file for {back_path} to {blob.public_url}')
                blob.upload_from_filename(back_path)

                # Info to save to firestore.
                background_info['background']['path'][color] = blob.public_url
                background_info['background']['median'][color] = back_data.background_median
                background_info['background']['rms'][color] = back_data.background_rms_median

            # Record background details in image.
            image_doc_snap.reference.set(background_info, merge=True)
    except Exception as e:
        print(f'Problem getting background for {local_path}: {e!r}')

    print(f'Creating new background subtracted file for {local_path}')
    # Save subtracted file locally.
    hdu = fits.PrimaryHDU(data=subtracted_data, header=header)

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
    hdu = fits.PrimaryHDU(data=subtracted_data, header=solved_header)

    hdu.writeto(solved_file, overwrite=True)

    print(f'Compressing: {solved_file}')
    with suppress(FileNotFoundError):
        os.unlink(local_path)
    new_local_path = fits_utils.fpack(solved_file)

    print(f'Returning: {new_local_path}')
    return new_local_path


def add_header_to_db(image_doc_snap, header):
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

        try:
            image_status = image_doc_snap.get('status')
        except KeyError:
            image_status = 'receiving_files'

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
                image_doc_snap.reference.set(image_data, merge=True)
            except Exception as e:
                print(f"Can't insert image info {image_id}: {e!r}")
        else:
            print(f'Image exists with status={image_status} so not updating record details')

    except Exception as e:
        raise e

    return True


if __name__ == '__main__':
    main()
