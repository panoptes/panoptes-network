import os
import time
from contextlib import suppress

from dateutil.parser import parse as parse_date

from google.cloud import logging
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub

from psycopg2.extras import execute_values
from psycopg2 import IntegrityError

import pandas as pd
from astropy.io import fits

from pocs.utils.images import fits as fits_utils
from piaa.utils.postgres import get_cursor
from piaa.utils import helpers
from piaa.utils import pipeline

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

# Pubsub
PUBSUB_PATH = os.getenv('SUB_TOPIC', 'gce-plate-solver')
subscriber_client = pubsub.SubscriberClient()
pubsub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_PATH}'

# BigQuery
bq_client = bigquery.Client()
bq_observations_dataset_ref = bq_client.dataset('observations')
bq_sources_table = bq_observations_dataset_ref.table('data')

# Logging
logging_client = logging.Client()
logging_client.setup_logging()
import logging


def main():
    logging.info(f"Starting pubsub listen on {pubsub_path}")

    try:
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            pubsub_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        logging.info(f"Plate-solver subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        logging.info(f'Problem starting subscriber: {e!r}')
        future.cancel()


def msg_callback(message):

    attributes = message.attributes
    bucket_path = attributes['bucket_path']
    object_id = attributes['object_id']

    try:
        # Get DB cursors
        catalog_db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')
        metadata_db_cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

        logging.info(f'Solving {bucket_path}')
        solve_file(bucket_path, object_id, catalog_db_cursor, metadata_db_cursor)
    finally:
        message.ack()
        catalog_db_cursor.close()
        metadata_db_cursor.close()


def solve_file(bucket_path, object_id, catalog_db_cursor, metadata_db_cursor):

    try:  # Wrap everything so we can do file cleanup

        unit_id, field, cam_id, seq_time, file = bucket_path.split('/')
        img_time = file.split('.')[0]
        image_id = f'{unit_id}_{cam_id}_{img_time}'

        # Don't process pointing images.
        if 'pointing' in bucket_path:
            logging.info(f'Skipping pointing file.')
            update_state('skipped', image_id=image_id, cursor=metadata_db_cursor)
            return

        # Don't process files that have been processed.
        img_state = get_state('sources_detected', image_id=image_id, cursor=metadata_db_cursor)
        if img_state == 'sources_extracted':
            logging.info(f'Skipping already processed image.')
            return

        # Download file blob from bucket
        logging.info(f'Downloading {bucket_path}')
        fz_fn = download_blob(bucket_path, destination='/tmp', bucket=bucket)

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
            logging.info(f'File not solved, skipping: {fits_fn} {e!r}')
            is_solved = False
        else:
            logging.info(f'Solved {fits_fn}')
            is_solved = True

        if not is_solved:
            update_state('unsolved', image_id=image_id, cursor=metadata_db_cursor)
            return

        # Lookup point sources
        logging.info(f'Looking up sources for {fits_fn}')
        point_sources = pipeline.lookup_point_sources(
            fits_fn,
            force_new=True,
            cursor=catalog_db_cursor
        )
        # Adjust some of the header items
        point_sources['gcs_file'] = object_id
        point_sources['image_id'] = image_id
        point_sources['seq_time'] = seq_time
        point_sources['img_time'] = img_time
        logging.info(f'Sources detected: {len(point_sources)} {fz_fn}')

        update_state('sources_detected', image_id=image_id, cursor=metadata_db_cursor)

        # Get frame sources
        get_sources(point_sources, fits_fn, cursor=metadata_db_cursor)
        update_state('sources_extracted', image_id=image_id, cursor=metadata_db_cursor)

        # Upload solved file if newly solved (i.e. nothing besides filename in wcs_info)
        if solve_info is not None and len(wcs_info) == 1:
            fz_fn = fits_utils.fpack(fits_fn)
            upload_blob(fz_fn, bucket_path, bucket=bucket)

    except Exception as e:
        logging.info(f'Error while solving field: {e!r}')
    finally:
        # Remove files
        for fn in [fits_fn, fz_fn]:
            with suppress(FileNotFoundError):
                os.remove(fn)

    return


def get_sources(point_sources, fits_fn, stamp_size=10, cursor=None):
    """Get postage stamps for each PICID in the given file.

    Args:
        point_sources (`pandas.DataFrame`): A DataFrame containing the results from `sextractor`.
        fits_fn (str): The name of the FITS file to extract stamps from.
        stamp_size (int, optional): The size of the stamp to extract, default 10 pixels.
        cursor (`psycopg2.Cursor`, optional): The DB cursor for the metadata database.
    """
    # Get the data for the entire frame
    data = fits.getdata(fits_fn)

    source_metadata = list()
    sources = list()

    remove_columns = ['picid', 'image_id', 'ra', 'dec',
                      'x_image', 'y_image', 'seq_time', 'img_time']

    # Loop each source
    logging.info(f'Starting stamp collection for {fits_fn}')

    logging.info(f'Getting point sources')
    # Loop through each frame
    for picid, row in point_sources.iterrows():
        # Get the stamp for the target
        target_slice = helpers.get_stamp_slice(
            row.x, row.y,
            stamp_size=(stamp_size, stamp_size),
            ignore_superpixel=False,
            verbose=False
        )

        # Add the target slice to metadata to preserve original location.
        row['target_slice'] = target_slice

        # Explicit type casting to match bigquery table schema.
        source_data = [(
            int(picid),
            parse_date(row.seq_time),
            parse_date(row.img_time),
            int(i),
            float(val)
        )
            for i, val
            in enumerate(data[target_slice].flatten())
        ]
        sources.extend(source_data)

        # Metadata for the detection, with most of row dumped into jsonb `metadata`.
        source_metadata.append({
            'picid': picid,
            'image_id': row.image_id,
            'astro_coords': f'({row.ra}, {row.dec})',
            'metadata': row.drop(remove_columns, errors='ignore').to_json(),
        })

    if cursor is None or cursor.closed:
        cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

    # Bulk insert the sources_metadata.
    try:
        headers = ['picid', 'image_id', 'astro_coords', 'metadata']
        insert_sql = f'INSERT INTO sources ({",".join(headers)}) VALUES %s'
        insert_template = '(' + ','.join([f'%({h})s' for h in headers]) + ')'

        logging.info(f'Inserting {len(source_metadata)} metadata for {fits_fn}')
        execute_values(cursor, insert_sql, source_metadata, insert_template)
        cursor.connection.commit()
    except IntegrityError:
        logging.info(f'Sources information already loaded into database')
    finally:
        logging.info(f'Copy of metadata complete {fits_fn}')

    logging.info(f'Done inserting metadata, building dataframe for data.')
    try:
        stamp_df = pd.DataFrame(
            sources,
            columns=[
                'picid',
                'sequence_time',
                'image_time',
                'pixel_index',
                'pixel_value'
            ]).set_index(['picid', 'image_time'])
    except AssertionError:
        logging.info(f'Error writing dataframe to BigQuery, sending to bucket')
        logging.info(sources[0:2])
    else:
        logging.info(f'Done building dataframe, sending to BigQuery')
        job = bq_client.load_table_from_dataframe(stamp_df, bq_sources_table).result()
        job.result()  # Waits for table load to complete.
        if job.state != 'DONE':
            logging.info(f'Failed to send dataframe to BigQuery')


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

    insert_sql = f"""
                INSERT INTO {table} ({col_names_str})
                VALUES ({col_val_holders})
                ON CONFLICT (id)
                DO UPDATE SET {', '.join(update_cols)}
                """

    try:
        cursor.execute(insert_sql, col_values)
    except Exception:
        logging.info('Rolling back cursor and trying again')
        try:
            cursor.connection.rollback()
            cursor.execute(insert_sql, col_values)
        except Exception as e:
            logging.info(f"Error in insert (error): {e!r}")
            logging.info(f"Error in insert (sql): {insert_sql}")
            logging.info(f"Error in insert (kwargs): {kwargs!r}")
            return False
    else:
        logging.info(f'Insert success: {table}')
        return True


def update_state(state, sequence_id=None, image_id=None, cursor=None, **kwargs):
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

    if sequence_id is None and image_id is None:
        raise ValueError('Need either a sequence_id or an image_id to update state')

    table = 'sequences'
    field = sequence_id
    if sequence_id is None:
        table = 'images'
        field = image_id

    update_sql = f"""
                UPDATE {table}
                SET state=%s
                WHERE id=%s
                """
    try:
        cursor.execute(update_sql, [state, field])
    except Exception:
        try:
            cursor.connection.rollback()
            cursor.execute(update_sql, [state, field])
        except Exception as e:
            logging.info(f"Error in insert (error): {e!r}")
            logging.info(f"Error in insert (sql): {update_sql}")
            logging.info(f"Error in insert (kwargs): {kwargs!r}")
            return False

    return True


def get_state(state, sequence_id=None, image_id=None, cursor=None, **kwargs):
    """Gets the current `state` value for either a sequence or image.

    Returns:
        tuple|None: Returns the value of `state` or None.
    """

    if cursor is None or cursor.closed:
        cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

    if sequence_id is None and image_id is None:
        raise ValueError('Need either a sequence_id or an image_id to get state')

    table = 'sequences'
    field = sequence_id
    if sequence_id is None:
        table = 'images'
        field = image_id

    update_sql = f"SELECT state FROM {table} WHERE id=%s"
    try:
        cursor.execute(update_sql, [field])
        row = cursor.fetchone()
        return row['state']
    except Exception as e:
        logging.info(f"Error in insert (error): {e!r}")
        logging.info(f"Error in insert (sql): {update_sql}")
        logging.info(f"Error in insert (kwargs): {kwargs!r}")
        return None


if __name__ == '__main__':
    main()
