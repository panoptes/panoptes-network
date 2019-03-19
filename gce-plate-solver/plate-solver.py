import os
import time
from contextlib import suppress

from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub

from dateutil.parser import parse as parse_date
from psycopg2.extras import execute_values
from psycopg2 import IntegrityError
from astropy.io import fits

import csv

from pocs.utils.images import fits as fits_utils
from piaa.utils.postgres import get_cursor
from piaa.utils import pipeline
from piaa.utils import helpers

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'gce-plate-solver')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'

# BigQuery
bq_client = bigquery.Client()
bq_observations_dataset_ref = bq_client.dataset('observations')
bq_sources_table = bq_observations_dataset_ref.table('data')


def main():
    print(f"Starting pubsub listen on {pubsub_sub_path}")

    try:
        flow_control = pubsub.types.FlowControl(max_messages=1)
        future = subscriber_client.subscribe(
            pubsub_sub_path, callback=msg_callback, flow_control=flow_control)

        # Keeps main thread from exiting.
        print(f"Plate-solver subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        print(f'Problem starting subscriber: {e!r}')
        future.cancel()


def msg_callback(message):

    attributes = message.attributes
    bucket_path = attributes['bucket_path']
    object_id = attributes['object_id']

    try:
        # Get DB cursors
        catalog_db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')
        metadata_db_cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')

        print(f'Solving {bucket_path}')
        solve_file(bucket_path, object_id, catalog_db_cursor, metadata_db_cursor)
    finally:
        print(f'Finished processing {object_id}.')
        catalog_db_cursor.close()
        metadata_db_cursor.close()
        # Acknowledge message
        message.ack()


def solve_file(bucket_path, object_id, catalog_db_cursor, metadata_db_cursor):

    try:  # Wrap everything so we can do file cleanup

        unit_id, field, cam_id, seq_time, file = bucket_path.split('/')
        img_time = file.split('.')[0]
        image_id = f'{unit_id}_{cam_id}_{img_time}'

        # Don't process pointing images.
        if 'pointing' in bucket_path:
            print(f'Skipping pointing file.')
            update_state('skipped', image_id=image_id, cursor=metadata_db_cursor)
            return

        # Don't process files that have been processed.
        img_state = get_state(image_id=image_id, cursor=metadata_db_cursor)
        if img_state == 'sources_extracted':
            print(f'Skipping already processed image.')
            return

        # Download file blob from bucket
        print(f'Downloading {bucket_path}')
        fz_fn = download_blob(bucket_path, destination='/tmp', bucket=bucket)

        # Unpack the FITS file
        print(f'Unpacking {fz_fn}')
        fits_fn = fits_utils.fpack(fz_fn, unpack=True)
        if not os.path.exists(fits_fn):
            update_state('error_unpacking', image_id=image_id, cursor=metadata_db_cursor)
            raise Exception(f'Problem unpacking {fz_fn}')

        # Check for existing WCS info
        print(f'Getting existing WCS for {fits_fn}')
        wcs_info = fits_utils.get_wcsinfo(fits_fn)
        already_solved = len(wcs_info) > 1

        if not already_solved:
            # Solve fits file
            print(f'Plate-solving {fits_fn}')
            try:
                solve_info = fits_utils.get_solve_field(
                    fits_fn, skip_solved=False, overwrite=True, timeout=90)
                print(f'Solved {fits_fn}')
            except Exception as e:
                print(f'File not solved, skipping: {fits_fn} {e!r}')
                update_state('error_solving', image_id=image_id, cursor=metadata_db_cursor)

            # Upload solved file if newly solved (i.e. nothing besides filename in wcs_info)
            if solve_info is not None and len(wcs_info) == 1:
                fz_fn = fits_utils.fpack(fits_fn)
                upload_blob(fz_fn, bucket_path, bucket=bucket)

        else:
            print(f'Found existing WCS for {fz_fn}')

        # Lookup point sources
        try:
            print(f'Looking up sources for {fits_fn}')
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
            point_sources['unit_id'] = unit_id
            point_sources['camera_id'] = cam_id
            print(f'Sources detected: {len(point_sources)} {fz_fn}')
            update_state('sources_detected', image_id=image_id, cursor=metadata_db_cursor)
        except Exception as e:
            update_state('error_sources_detection', image_id=image_id, cursor=metadata_db_cursor)
            raise e

        print(f'Looking up sources for {fz_fn}')
        get_sources(point_sources, fits_fn, cursor=metadata_db_cursor)
        update_state('sources_extracted', image_id=image_id, cursor=metadata_db_cursor)

    except Exception as e:
        print(f'Error while solving field: {e!r}')
        return False
    finally:
        print(f'Solve and extraction complete, cleaning up for {object_id}')
        # Remove files
        for fn in [fits_fn, fz_fn]:
            with suppress(FileNotFoundError):
                os.remove(fn)

    return True


def get_sources(point_sources, fits_fn, stamp_size=10, cursor=None):
    """Get postage stamps for each PICID in the given file.

    Args:
        point_sources (`pandas.DataFrame`): A DataFrame containing the results from `sextractor`.
        fits_fn (str): The name of the FITS file to extract stamps from.
        stamp_size (int, optional): The size of the stamp to extract, default 10 pixels.
        cursor (`psycopg2.Cursor`, optional): The DB cursor for the metadata database.
    """
    data = fits.getdata(fits_fn)
    image_id = None

    source_metadata = list()

    remove_columns = ['picid', 'image_id', 'ra', 'dec',
                      'x_image', 'y_image', 'seq_time', 'img_time']

    print(f'Getting point sources')

    row = point_sources.iloc[0]
    sources_csv_fn = f'{row.unit_id}-{row.camera_id}-{row.seq_time}-{row.img_time}.csv'
    print(f'Sources data will be extracted to {sources_csv_fn}')

    print(f'Starting source extraction for {fits_fn}')
    with open(sources_csv_fn, 'w') as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)

        # Write out headers.
        csv_headers = ['picid', 'unit_id', 'camera_id', 'sequence_time', 'image_time']
        # Add column headers for flattened stamp.
        csv_headers.extend([f'pixel_{i:02d}' for i in range(stamp_size**2)])
        writer.writerow(csv_headers)

        for picid, row in point_sources.iterrows():
            image_id = row.image_id

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
            stamp = data[target_slice].flatten().tolist()

            row_values = [
                int(picid),
                str(row.unit_id),
                str(row.camera_id),
                parse_date(row.seq_time),
                parse_date(row.img_time),
            ]
            row_values.extend(stamp)

            # Write out stamp data
            writer.writerow(row_values)

            # Metadata for the detection, with most of row dumped into jsonb `metadata`.
            source_metadata.append({
                'picid': picid,
                'image_id': row.image_id,
                'astro_coords': f'({row.ra}, {row.dec})',
                'metadata': row.drop(remove_columns, errors='ignore').to_json(),
            })

    # Bulk insert the sources_metadata.
    try:
        headers = ['picid', 'image_id', 'astro_coords', 'metadata']
        insert_sql = f'INSERT INTO sources ({",".join(headers)}) VALUES %s'
        insert_template = '(' + ','.join([f'%({h})s' for h in headers]) + ')'

        print(f'Inserting {len(source_metadata)} metadata for {fits_fn}')
        execute_values(cursor, insert_sql, source_metadata, insert_template)
        cursor.connection.commit()
    except IntegrityError:
        print(f'Sources information already loaded into database')
    finally:
        update_state('metadata_inserted', image_id=image_id, cursor=cursor)
        print(f'Copy of metadata complete {fits_fn}')

    try:
        upload_blob(sources_csv_fn, destination=sources_csv_fn.replace('-', '/'),
                    bucket_name='panoptes-detected-sources')
    except Exception as e:
        print(f'Uploading of sources failed for {fits_fn}')
        update_state('error_uploading_sources', image_id=image_id, cursor=cursor)
    finally:
        with suppress(FileNotFoundError):
            print(f'Cleaning up {sources_csv_fn}')
            os.remove(sources_csv_fn)

    return image_id


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

    print('Blob {} downloaded to {}.'.format(source_blob_name, destination))

    return destination


def upload_blob(source_file_name, destination, bucket=None, bucket_name='panoptes-survey'):
    """Uploads a file to the bucket."""
    print('Uploading {} to {}.'.format(source_file_name, destination))

    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination))


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
        cursor.connection.commit()
    except Exception:
        print('Rolling back cursor and trying again')
        try:
            cursor.connection.rollback()
            cursor.execute(insert_sql, col_values)
            cursor.connection.commit()
        except Exception as e:
            print(f"Error in insert (error): {e!r}")
            print(f"Error in insert (sql): {insert_sql}")
            print(f"Error in insert (kwargs): {kwargs!r}")
            return False
    else:
        print(f'Insert success: {table}')
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
        cursor.connection.commit()
        print(f'{field} set to state {state}')
    except Exception:
        try:
            print(f'Updating of state ({field}={state}) failed, rolling back and trying again')
            cursor.connection.rollback()
            cursor.execute(update_sql, [state, field])
            cursor.connection.commit()
            print(f'{field} set to state {state}')
        except Exception as e:
            print(f"Error in insert (error): {e!r}")
            print(f"Error in insert (sql): {update_sql}")
            print(f"Error in insert (kwargs): {kwargs!r}")
            return False

    return True


def get_state(sequence_id=None, image_id=None, cursor=None, **kwargs):
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
        print(f"Error in insert (error): {e!r}")
        print(f"Error in insert (sql): {update_sql}")
        print(f"Error in insert (kwargs): {kwargs!r}")
        return None


if __name__ == '__main__':
    main()
