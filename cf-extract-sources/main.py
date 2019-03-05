import os
from flask import jsonify
import pandas as pd

from psycopg2.extras import execute_values
from psycopg2 import IntegrityError
from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool

from astropy.io import fits

from google.cloud import logging
from google.cloud import storage

from piaa.utils import helpers

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Cloud SQL
CONNECTION_NAME = os.getenv(
    'INSTANCE_CONNECTION_NAME',
    'panoptes-survey:us-central1:panoptes-meta'
)
DB_USER = os.getenv('POSTGRES_USER', 'panoptes')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)
DB_NAME = os.getenv('POSTGRES_DATABASE', 'metadata')

pg_config = {
    'user': DB_USER,
    'password': DB_PASSWORD,
    'dbname': DB_NAME
}

# Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

# Connection pools reuse connections between invocations,
# and handle dropped or expired connections automatically.
pg_pool = None


def extract_sources(request):
    """Look for uploaded files and process according to the file type.

    Triggered when file is uploaded to bucket.

    FITS: Set header variables and then forward to endpoint for adding headers
    to the metadatabase. The header is looked up from the file id, including the
    storage bucket file generation id, which are stored into the headers.

    CR2: Trigger creation of timelapse and jpg images.

    Example file id:

    panoptes-survey/PAN001/M42/14d3bd/20181011T134202/20181011T134333.fits.fz/1539272833023747

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    request_json = request.get_json()

    csv_bucket_path = request_json.get('sources_file')

    if csv_bucket_path is None:
        return f'No file requested'

    print(f"Processing {csv_bucket_path}")
    local_csv = download_blob(csv_bucket_path, bucket_name='panoptes-detected-sources')
    point_sources = pd.read_csv(local_csv)

    global pg_pool

    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect(f'/cloudsql/{CONNECTION_NAME}')
        except OperationalError as e:
            print(e)
            # If production settings fail, use local development ones
            __connect('localhost')

    conn = pg_pool.getconn()
    conn.set_isolation_level(0)
    with conn.cursor() as cursor:
        image_id = get_sources(point_sources, cursor=cursor)
        update_state('sources_extracted', image_id=image_id, cursor=cursor)

    return jsonify(success=True, msg=f"Image processed: {csv_bucket_path}")


def get_sources(point_sources, stamp_size=10, cursor=None):
    """Get postage stamps for each PICID in the given file.

    Args:
        point_sources (`pandas.DataFrame`): A DataFrame containing the results from `sextractor`.
        fits_fn (str): The name of the FITS file to extract stamps from.
        stamp_size (int, optional): The size of the stamp to extract, default 10 pixels.
        cursor (`psycopg2.Cursor`, optional): The DB cursor for the metadata database.
    """
    data = None
    fits_fn = None
    image_id = None

    source_metadata = list()
    sources = list()

    remove_columns = ['picid', 'image_id', 'ra', 'dec',
                      'x_image', 'y_image', 'seq_time', 'img_time']

    logging.info(f'Getting point sources')

    for picid, row in point_sources.iterrows():
        image_id = row.image_id

        # Get the data if we don't have it.
        fits_bucket_name = row.gcs_file.replace('panoptes-survey', '')
        if data is None or fits_bucket_name != fits_fn:
            fits_fn = download_blob(fits_bucket_name, destination='/tmp')
            data = fits.getdata(fits_fn)
            fits_bucket_name = fits_fn

        # Get the stamp for the target
        target_slice = helpers.get_stamp_slice(
            row.x, row.y,
            stamp_size=(stamp_size, stamp_size),
            ignore_superpixel=False,
            verbose=False
        )

        # Add the target slice to metadata to preserve original location.
        row['target_slice'] = target_slice

        # # Explicit type casting to match bigquery table schema.
        # source_data = [(
        #     int(picid),
        #     str(row.unit_id),
        #     str(row.camera_id),
        #     parse_date(row.seq_time),
        #     parse_date(row.img_time),
        #     int(row.x),
        #     int(row.y),
        #     int(i),
        #     float(val)
        # )
        #     for i, val
        #     in enumerate(data[target_slice].flatten())
        # ]
        # sources.extend(source_data)

        # Metadata for the detection, with most of row dumped into jsonb `metadata`.
        sources.append({
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

        logging.info(f'Inserting {len(source_metadata)} metadata for {fits_fn}')
        execute_values(cursor, insert_sql, source_metadata, insert_template)
        cursor.connection.commit()
    except IntegrityError:
        logging.info(f'Sources information already loaded into database')
    finally:
        logging.info(f'Copy of metadata complete {fits_fn}')

    # logging.info(f'Done inserting metadata, building dataframe for data.')
    # try:
    #     stamp_df = pd.DataFrame(
    #         sources,
    #         columns=[
    #             'picid',
    #             'panid',
    #             'camera_id',
    #             'sequence_time',
    #             'image_time',
    #             'image_x',
    #             'image_y',
    #             'pixel_index',
    #             'pixel_value'
    #         ]).set_index(['picid', 'image_time'])
    # except AssertionError as e:
    #     logging.info(f'Error writing dataframe to BigQuery: {e!r}')
    # else:
    #     logging.info(f'Done building dataframe, sending to BigQuery')
    #     job = bq_client.load_table_from_dataframe(stamp_df, bq_sources_table)
    #     job.result()  # Waits for table load to complete.
    #     if job.state != 'DONE':
    #         logging.info(f'Failed to send dataframe to BigQuery')

    return image_id


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


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)
