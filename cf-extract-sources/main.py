import os
from flask import jsonify
import pandas as pd

from decimal import Decimal

from psycopg2.extras import execute_values
from psycopg2 import IntegrityError
from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool

from google.cloud import storage

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
    local_csv = download_blob(csv_bucket_path, destination='/tmp',
                              bucket_name='panoptes-detected-sources')
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
        try:
            image_id = get_sources(point_sources, cursor=cursor)
            update_state('sources_extracted', image_id=image_id, cursor=cursor)
        except Exception as e:
            return jsonify(success=False,
                           msg=f"Error in processing image: {csv_bucket_path} {e!r}")
        finally:
            cursor.close()
            pg_pool.putconn(conn)

    return jsonify(success=True, msg=f"Image processed: {csv_bucket_path}")


def get_sources(point_sources, stamp_size=10, cursor=None):
    """Get postage stamps for each PICID in the given file.

    Args:
        point_sources (`pandas.DataFrame`): A DataFrame containing the results from `sextractor`.
        stamp_size (int, optional): The size of the stamp to extract, default 10 pixels.
        cursor (`psycopg2.Cursor`, optional): The DB cursor for the metadata database.
    """
    image_id = None

    source_metadata = list()

    remove_columns = ['picid', 'image_id', 'ra', 'dec',
                      'x_image', 'y_image', 'seq_time', 'img_time']

    print(f'Getting point sources')

    for picid, row in point_sources.iterrows():
        image_id = row.image_id

        # Get the stamp for the target
        target_slice = get_stamp_slice(
            row.x, row.y,
            stamp_size=(stamp_size, stamp_size),
            ignore_superpixel=False,
            verbose=False
        )

        # Add the target slice to metadata to preserve original location.
        row['target_slice'] = target_slice

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

        print(f'Inserting {len(source_metadata)} metadata for {image_id}')
        execute_values(cursor, insert_sql, source_metadata, insert_template)
        cursor.connection.commit()
    except IntegrityError:
        print(f'Sources information already loaded into database')
    finally:
        print(f'Copy of metadata complete {image_id}')

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
            print(f"Error in insert (error): {e!r}")
            print(f"Error in insert (sql): {update_sql}")
            print(f"Error in insert (kwargs): {kwargs!r}")
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

    print('Blob {} downloaded to {}.'.format(source_blob_name, destination))

    return destination


def get_stamp_slice(x, y, stamp_size=(14, 14), verbose=False, ignore_superpixel=False):
    """Get the slice around a given position with fixed Bayer pattern.

    Given an x,y pixel position, get the slice object for a stamp of a given size
    but make sure the first position corresponds to a red-pixel. This means that
    x,y will not necessarily be at the center of the resulting stamp.

    Args:
        x (float): X pixel position.
        y (float): Y pixel position.
        stamp_size (tuple, optional): The size of the cutout, default (14, 14).
        verbose (bool, optional): Verbose, default False.

    Returns:
        `slice`: A slice object for the data.
    """
    # Make sure requested size can have superpixels on each side.
    if not ignore_superpixel:
        for side_length in stamp_size:
            side_length -= 2  # Subtract center superpixel
            if int(side_length / 2) % 2 != 0:
                print("Invalid slice size: ", side_length + 2,
                      " Slice must have even number of pixels on each side of",
                      " the center superpixel.",
                      "i.e. 6, 10, 14, 18...")
                return

    # Pixels have nasty 0.5 rounding issues
    x = Decimal(float(x)).to_integral()
    y = Decimal(float(y)).to_integral()
    color = pixel_color(x, y)
    if verbose:
        print(x, y, color)

    x_half = int(stamp_size[0] / 2)
    y_half = int(stamp_size[1] / 2)

    x_min = int(x - x_half)
    x_max = int(x + x_half)

    y_min = int(y - y_half)
    y_max = int(y + y_half)

    # Alter the bounds depending on identified center pixel
    if color == 'B':
        x_min -= 1
        x_max -= 1
        y_min -= 0
        y_max -= 0
    elif color == 'G1':
        x_min -= 1
        x_max -= 1
        y_min -= 1
        y_max -= 1
    elif color == 'G2':
        x_min -= 0
        x_max -= 0
        y_min -= 0
        y_max -= 0
    elif color == 'R':
        x_min -= 0
        x_max -= 0
        y_min -= 1
        y_max -= 1

    # if stamp_size is odd add extra
    if (stamp_size[0] % 2 == 1):
        x_max += 1
        y_max += 1

    if verbose:
        print(x_min, x_max, y_min, y_max)
        print()

    return (slice(y_min, y_max), slice(x_min, x_max))


def pixel_color(x, y):
    """ Given an x,y position, return the corresponding color.

    The Bayer array defines a superpixel as a collection of 4 pixels
    set in a square grid:

                     R G
                     G B

    `ds9` and other image viewers define the coordinate axis from the
    lower left corner of the image, which is how a traditional x-y plane
    is defined and how most images would expect to look when viewed. This
    means that the `(0, 0)` coordinate position will be in the lower left
    corner of the image.

    When the data is loaded into a `numpy` array the data is flipped on the
    vertical axis in order to maintain the same indexing/slicing features.
    This means the the `(0, 0)` coordinate position is in the upper-left
    corner of the array when output. When plotting this array one can use
    the `origin='lower'` option to view the array as would be expected in
    a normal image although this does not change the actual index.

    Note:

        Image dimensions:

         ----------------------------
         x | width  | i | columns |  5208
         y | height | j | rows    |  3476

        Bayer Pattern:

                                      x / j

                      0     1    2     3 ... 5204 5205 5206 5207
                    --------------------------------------------
               3475 |  R   G1    R    G1        R   G1    R   G1
               3474 | G2    B   G2     B       G2    B   G2    B
               3473 |  R   G1    R    G1        R   G1    R   G1
               3472 | G2    B   G2     B       G2    B   G2    B
                  . |
         y / i    . |
                  . |
                  3 |  R   G1    R    G1        R   G1    R   G1
                  2 | G2    B   G2     B       G2    B   G2    B
                  1 |  R   G1    R    G1        R   G1    R   G1
                  0 | G2    B   G2     B       G2    B   G2    B


        This can be described by:

                 | row (y) |  col (x)
             --------------| ------
              R  |  odd i, |  even j
              G1 |  odd i, |   odd j
              G2 | even i, |  even j
              B  | even i, |   odd j

            bayer[1::2, 0::2, 0] = 1 # Red
            bayer[1::2, 1::2, 1] = 1 # Green
            bayer[0::2, 0::2, 1] = 1 # Green
            bayer[0::2, 1::2, 2] = 1 # Blue

    Returns:
        str: one of 'R', 'G1', 'G2', 'B'
    """
    x = int(x)
    y = int(y)
    if x % 2 == 0:
        if y % 2 == 0:
            return 'G2'
        else:
            return 'R'
    else:
        if y % 2 == 0:
            return 'B'
        else:
            return 'G1'


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)
