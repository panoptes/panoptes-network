import os
import flask
from collections import defaultdict

from decimal import Decimal
from datetime import datetime

from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

from google.cloud import storage


# Storage Bucket
PROJECT_ID = os.getenv('POSTGRES_USER', 'panoptes')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)

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

# Connection pools reuse connections between invocations,
# and handle dropped or expired connections automatically.
pg_pool = None


def get_observations_data(request):
    """ENTRYPOINT - get the observation data """
    request_json = request.get_json() or dict()

    sequence_id = None
    if request_json and 'sequence_id' in request_json:
        sequence_id = request_json['sequence_id']
    elif request.args and 'sequence_id' in request.args:
        sequence_id = request.args['sequence_id']

    # Used for looking up existing file.
    json_bucket_location = None

    if sequence_id:
        print("Looking up observations for sequence_id={}".format(sequence_id))
        # Lookup information about each image from the database.
        images = get_images(sequence_id)

        # Lookup information about the observation as a whole.
        sequence = get_observation_info(sequence_id)
        sequence_files = defaultdict(list)
        items = {
            "images": images,
            "sequence": sequence
        }

        # Get the actual directory in the storage bucket.
        sequence_dir = ''
        if images[0]['file_path'] > '':
            try:
                sequence_dir = os.path.join(*images[0]['file_path'].split('/')[4:8])
                items['sequence_dir'] = sequence_dir
                print("Seq dir: ", sequence_dir)
                json_bucket_location = os.path.join(sequence_dir, 'observation_info.json')
            except IndexError:
                print("No rows")

        if sequence_dir > '':
            print("Looking for files in {}".format(sequence_dir))
            for blob in bucket.list_blobs(prefix=sequence_dir):
                filename = os.path.basename(blob.name)
                _, ext = os.path.splitext(filename)
                sequence_files[ext.replace('.', '')].append(blob.public_url)

            items['sequence_files'] = sequence_files
    elif 'search_observations' in request_json:
        items = search_sequences(request_json)
    else:
        items = get_sequences(request_json)

    print("Found {} rows".format(len(items)))
    response_json = dict(items=items, total=len(items))

    body = flask.json.dumps(response_json, default=json_decoder)

    # Store the json document for next time.
    if json_bucket_location:
        print(f'Uploading observation json to {json_bucket_location}')
        try:
            upload_json_string(body, json_bucket_location)
            print(f'Upload complete')
        except Exception as e:
            print(f"Problem with upload {e}")

    headers = {
        'content-type': "application/json",
        'Access-Control-Allow-Origin': "*",
    }

    return (body, headers)


def get_sequences(params):
    global pg_pool

    num_days = params.get('num_days', 21)
    min_image_count = params.get('min_image_count', 5)

    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect('/cloudsql/{}'.format(CONNECTION_NAME))
        except OperationalError as e:
            print(e)
            # If production settings fail, use local development ones
            __connect('localhost')

    conn = pg_pool.getconn()
    conn.set_isolation_level(0)

    select_sql = f"""
        SELECT
            t1.id,
            t1.exptime,
            t1.field,
            t1.pocs_version,
            t1.start_date,
            t1.unit_id,
            count(t2.id) as image_count
        FROM sequences t1, images t2
        WHERE t1.id=t2.sequence_id
            AND t1.start_date > CURRENT_DATE - interval '{num_days} days'
        GROUP BY t1.id
        HAVING count(t2.id) >= {min_image_count}
        ORDER BY t1.start_date DESC
        """

    rows = list()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            cursor.close()
    finally:
        pg_pool.putconn(conn)

    return rows


def search_sequences(params):
    global pg_pool

    ra_search = float(params['ra'])  # degrees
    dec_search = float(params['dec'])  # degrees
    search_radius = params.get('search_radius', 5)  # degrees

    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect('/cloudsql/{}'.format(CONNECTION_NAME))
        except OperationalError as e:
            print(e)
            # If production settings fail, use local development ones
            __connect('localhost')

    conn = pg_pool.getconn()
    conn.set_isolation_level(0)

    select_sql = f"""
        SELECT
            t1.id,
            t1.exptime,
            t1.field,
            t1.pocs_version,
            t1.start_date,
            t1.unit_id,
            count(t2.id) as image_count
        FROM sequences t1, images t2
        WHERE t1.id=t2.sequence_id
            AND t1.id IN (
                SELECT distinct(sequence_id)
                FROM sequences
                WHERE
                    ra_mnt >= {ra_search - search_radius}
                    AND
                    ra_mnt <= {ra_search + search_radius}
                    AND
                    dec_mnt >= {dec_search - search_radius}
                    AND
                    dec_mnt <= {dec_search + search_radius}
            )
        GROUP BY t1.id
        ORDER BY t1.start_date DESC
        """

    rows = list()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            cursor.close()
    finally:
        pg_pool.putconn(conn)

    return rows


def get_images(sequence_id):
    global pg_pool

    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect('/cloudsql/{}'.format(CONNECTION_NAME))
        except OperationalError as e:
            print(e)
            # If production settings fail, use local development ones
            __connect('localhost')

    conn = pg_pool.getconn()
    conn.set_isolation_level(0)

    select_sql = """
        SELECT
            t1.exptime,
            t1.file_path,
            t1.ha_mnt,
            t1.headers->>'AIRMASS' as airmass,
            headers->>'IMGTIME' as imgtime,
            headers->>'MOONFRAC' as moonfrac,
            headers->>'MOONSEP' as moonsep
        FROM images t1
        WHERE sequence_id=%s
        ORDER BY imgtime DESC
        """

    rows = list()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(select_sql, (sequence_id, ))
        rows = cursor.fetchall()
        cursor.close()

    pg_pool.putconn(conn)

    return rows


def get_observation_info(sequence_id):
    global pg_pool

    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect('/cloudsql/{}'.format(CONNECTION_NAME))
        except OperationalError as e:
            print(e)
            # If production settings fail, use local development ones
            __connect('localhost')

    conn = pg_pool.getconn()
    conn.set_isolation_level(0)

    select_sql = """
        SELECT t1.*, count(t2.id) as image_count
        FROM sequences t1, images t2
        WHERE t1.id=%s
        AND t1.id=t2.sequence_id
        GROUP BY t1.id
        ORDER BY t1.start_date DESC
        """

    rows = list()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(select_sql, (sequence_id, ))
            rows = cursor.fetchone()
            cursor.close()
    finally:
        pg_pool.putconn(conn)

    return rows


def json_decoder(o):
    if isinstance(o, Decimal):
        return float(o)
    elif isinstance(o, datetime):
        return o.isoformat()


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)


def upload_json_string(string_content, destination_blob_name):
    """Uploads a json string to the the bucket."""
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(string_content, content_type='application/json')
