import os
import sys
import time
from contextlib import suppress

from google.cloud import logging
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub

import pandas as pd
from astropy import units as u
from astropy.time import Time
from astropy.io import fits

from pocs.utils.images import fits as fits_utils
from piaa.utils.postgres import get_cursor
from piaa.utils import helpers
from piaa.utils import pipeline

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
SUBSCRIPTION_PATH = os.getenv('SUB_TOPIC', 'plate-solver-sub')

logging_client = logging.Client()
bq_client = bigquery.Client()
storage_client = storage.Client(project=PROJECT_ID)
subscriber_client = pubsub.SubscriberClient()

bucket = storage_client.get_bucket(BUCKET_NAME)

subscription_path = f'projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_PATH}'

logging_client.setup_logging()

import logging


def main():
    logging.info(f"Starting pubsub listen on {subscription_path}")

    try:
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            subscription_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        logging.info(f"Subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        logging.info(f'Problem starting subscriber: {e!r}')
        future.cancel()


def msg_callback(message):
    catalog_db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')
    metadata_db_cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

    attributes = message.attributes

    event_type = attributes['eventType']
    object_id = attributes['objectId']
    overwrote_generation = attributes['overwroteGeneration']

    new_file = event_type == 'OBJECT_FINALIZE' and overwrote_generation == ""

    logging.info(f'Event Type: {event_type} New file?: {new_file} File: {object_id}')

    try:
        if new_file:
            # TODO: Add CR2 handling
            if object_id.endswith('.fz') or object_id.endswith('.fits'):
                logging.info(f'Solving {object_id}')
                status = solve_file(object_id, catalog_db_cursor, metadata_db_cursor)
                # TODO(wtgee): Handle partial failures
                if status['status'] == 'sources_extracted':
                    logging.info(f'File solved, sending ack')
            else:
                logging.info('Not a FITS file')
        else:
            # If an overwrite then simply ack message
            logging.info('Not a new file, acknowledging message')
    finally:
        message.ack()
        catalog_db_cursor.close()
        metadata_db_cursor.close()


def solve_file(object_id, catalog_db_cursor, metadata_db_cursor):

    if 'pointing' in object_id:
        return {'status': 'skipped', 'filename': object_id, }

    try:  # Wrap everything so we can do file cleanup

        unit_id, field, cam_id, seq_time, file = object_id.split('/')
        image_time = file.split('.')[0]
        sequence_id = f'{unit_id}_{cam_id}_{seq_time}'
        image_id = f'{unit_id}_{cam_id}_{image_time}'

        # Download file blob from bucket
        logging.info(f'Downloading {object_id}')
        fz_fn = download_blob(object_id, destination='/tmp', bucket=bucket)

        # Check for existing WCS info
        logging.info(f'Getting existing WCS for {fz_fn}')
        wcs_info = fits_utils.get_wcsinfo(fz_fn)
        if len(wcs_info) > 1:
            logging.info(f'Found existing WCS for {fz_fn}')

        # Unpack the FITS file
        logging.info(f'Unpacking {fz_fn}')
        fits_fn = fits_utils.fpack(fz_fn, unpack=True)
        if not os.path.exists(fits_fn):
            raise Exception(f'Problem unpacking {fz_fn}')

        # Solve fits file
        logging.info(f'Plate-solving {fits_fn}')
        try:
            solve_info = fits_utils.get_solve_field(
                fits_fn, skip_solved=False, overwrite=True, timeout=90, verbose=True)
        except Exception as e:
            status = 'unsolved'
            logging.info(f'File not solved, skipping: {fits_fn} {e!r}')
            is_solved = False
        else:
            logging.info(f'Solved {fits_fn}')
            status = 'solved'
            is_solved = True

        # Adjust some of the header items
        logging.info('Adding header information to database')
        header = fits_utils.getheader(fits_fn)
        obstime = Time(pd.to_datetime(file.split('.')[0]))
        exptime = header['EXPTIME'] * u.second
        obstime += (exptime / 2)

        header['PANID'] = unit_id
        header['FIELD'] = field
        header['INSTRUME'] = cam_id
        header['SEQTIME'] = seq_time
        header['IMGTIME'] = image_time
        header['SEQID'] = sequence_id
        header['IMAGEID'] = image_id
        header['PSTATE'] = status
        if not add_header_to_db(header, metadata_db_cursor):
            logging.info('Problem adding headers to DB')

        if not is_solved:
            return {'status': status, 'filename': fits_fn, }

        # Lookup point sources
        logging.info(f'Looking up sources for {fits_fn}')
        point_sources = pipeline.lookup_point_sources(
            fits_fn,
            force_new=True,
            cursor=catalog_db_cursor
        )
        point_sources['obstime'] = str(obstime.datetime)
        point_sources['exptime'] = exptime
        point_sources['airmass'] = header['AIRMASS']
        point_sources['file'] = file
        point_sources['sequence'] = sequence_id
        point_sources['image_id'] = image_id

        # Get frame stamps
        logging.info('Get stamps for frame')
        stamps = get_stamps(point_sources, fits_fn, image_id)
        stamps_fn = os.path.join(unit_id, field, cam_id, seq_time, f'stamps-{image_time}.csv')
        local_stamps_fn = os.path.join('/tmp', stamps_fn.replace('/', '_'))
        stamps.to_csv(local_stamps_fn)
        upload_blob(local_stamps_fn, stamps_fn, bucket=bucket)

        # Send CSV to bucket
        bucket_csv = os.path.join(unit_id, field, cam_id, seq_time, f'sources-{image_time}.csv')
        local_csv = os.path.join('/tmp', bucket_csv.replace('/', '_'))
        logging.info(f'Sending {len(point_sources)} sources to CSV file {local_csv}')
        try:
            point_sources.to_csv(local_csv)
            upload_blob(local_csv, bucket_csv, bucket=bucket)
        except Exception as e:
            logging.info(f'Problem creating CSV: {e!r}')

        # Upload solved file if newly solved (i.e. nothing besides filename in wcs_info)
        if solve_info is not None and len(wcs_info) == 1:
            fz_fn = fits_utils.fpack(fits_fn)
            upload_blob(fz_fn, object_id, bucket=bucket)

        status = 'sources_extracted'
    except Exception as e:
        logging.info(f'Error while solving field: {e!r}')
        status = 'error'
    finally:
        # Remove files
        for fn in [fits_fn, fz_fn, local_csv]:
            with suppress(FileNotFoundError):
                os.remove(fn)

    return {'status': status, 'filename': fits_fn, }


def get_stamps(point_sources, fits_fn, image_id, stamp_size=10):
    # Create PICID stamps
    data = fits.getdata(fits_fn)

    stamps = list()

    # Loop each source
    for picid, target_table in point_sources.groupby('picid'):

        # Loop through each frame
        for idx, row in target_table.iterrows():
            # Get the data for the entire frame

            # Get the stamp for the target
            target_slice = helpers.get_stamp_slice(
                row.x, row.y,
                stamp_size=(stamp_size, stamp_size),
                ignore_superpixel=False,
                verbose=False
            )

            # Get data
            stamps.append({
                'image_id': row.image_id,
                'pic_id': picid,
                'date_obs': row.obstime,
                'ra': row.ra,
                'dec': row.dec,
                'original_position': [row.x, row.y],
                'data': data[target_slice].flatten()
            })

    # Write out the full PSC
    df0 = pd.DataFrame(stamps)
    return df0


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

    logging.info('Blob {} downloaded to {}.'.format(source_blob_name, destination))

    return destination


def upload_blob(source_file_name, destination, bucket=None, bucket_name='panoptes-survey'):
    """Uploads a file to the bucket."""
    logging.info('Uploading {} to {}.'.format(source_file_name, destination))

    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    logging.info('File {} uploaded to {}.'.format(source_file_name, destination))


def add_header_to_db(header, cursor):
    """Add FITS image info to metadb.

    Note:
        This function doesn't check header for proper entries and
        assumes a large list of keywords. See source for details.

    Args:
        header (dict): FITS Header data from an observation.
        conn (None, optional): DB connection, if None then `get_db_proxy_conn`
            is used.
        logger (None, optional): A logger.

    Returns:
        str: The image_id.
    """
    try:
        logging.info('Starting add_header')
        unit_id = int(header.get('PANID').replace('PAN', ''))
        seq_id = header.get('SEQID', '').strip()
        img_id = header.get('IMAGEID', '').strip()
        camera_id = header.get('INSTRUME', '').strip()

        unit_data = {
            'id': unit_id,
            'name': header.get('OBSERVER', '').strip(),
            'lat': float(header.get('LAT-OBS')),
            'lon': float(header.get('LONG-OBS')),
            'elevation': float(header.get('ELEV-OBS')),
        }
        if not meta_insert('units', cursor, **unit_data):
            logging.info('Problem inserting units info')
            return False

        camera_data = {
            'unit_id': unit_id,
            'id': camera_id,
        }
        if not meta_insert('cameras', cursor, **camera_data):
            logging.info('Problem inserting cameras info')
            return False

        seq_data = {
            'id': seq_id,
            'unit_id': unit_id,
            'start_date': header.get('SEQID', None).split('_')[-1],
            'exp_time': header.get('EXPTIME'),
            'ra_rate': header.get('RA-RATE'),
            'field': header.get('FIELD', ''),
            'pocs_version': header.get('CREATOR', ''),
            'piaa_state': header.get('PSTATE', 'header_received'),
        }

        try:
            if not meta_insert('sequences', cursor, **seq_data):
                logging.info('Problem inserting sequences info')
                return False
        except Exception as e:
            logging.info("Can't insert sequence: {}".format(seq_id))
            raise e

        image_data = {
            'id': img_id,
            'sequence_id': seq_id,
            'date_obs': header.get('DATE-OBS'),
            'ra_mnt': header.get('RA-MNT'),
            'ha_mnt': header.get('HA-MNT'),
            'dec_mnt': header.get('DEC-MNT'),
            'exp_time': header.get('EXPTIME'),
            'camera_id': camera_id,
            'file_path': header.get('FILENAME')
        }

        # Add plate-solved info.
        try:
            image_data['center_ra'] = header['CRVAL1']
            image_data['center_dec'] = header['CRVAL2']
        except KeyError:
            pass

        if not meta_insert('images', cursor, **image_data):
            logging.info('Problem inserting images info')
            return False
    except Exception as e:
        logging.info(f'Error in add header: {e!r}')
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.info(exc_type, fname, exc_tb.tb_lineno)
        raise e
    else:
        logging.info("Header added for SEQ={} IMG={}".format(seq_id, img_id))
        return img_id
    finally:
        cursor.close()


def meta_insert(table, cursor, **kwargs):
    """Inserts arbitrary key/value pairs into a table.

    Args:
        table (str): Table in which to insert.
        conn (None, optional): DB connection, if None then `get_db_proxy_conn`
            is used.
        logger (None, optional): A logger.
        **kwargs: List of key/value pairs corresponding to columns in the
            table.

    Returns:
        tuple|None: Returns the inserted row or None.
    """

    if cursor is None or cursor.closed:
        cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

    col_names = list()
    col_values = list()
    for name, value in kwargs.items():
        col_names.append(name)
        col_values.append(value)

    col_names_str = ','.join(col_names)
    col_val_holders = ','.join(['%s' for _ in range(len(col_values))])

    # Build update set
    update_cols = list()
    for col in col_names:
        if col in ['id']:
            continue
        update_cols.append('{0} = EXCLUDED.{0}'.format(col))

    insert_sql = '''INSERT INTO {} ({})
                    VALUES ({})
                    ON CONFLICT (id)
                    DO UPDATE SET {}
                    '''.format(
        table,
        col_names_str,
        col_val_holders,
        ', '.join(update_cols)
    )

    try:
        cursor.execute(insert_sql, col_values)
    except Exception as e:
        logging.info(f"Error in insert (error): {e!r}")
        logging.info(f"Error in insert (sql): {insert_sql}")
        logging.info(f"Error in insert (kwargs): {kwargs!r}")
        return False
    else:
        logging.info(f'Insert success: {table}')
        return True


if __name__ == '__main__':
    main()
