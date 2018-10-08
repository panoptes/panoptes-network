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
    request_json = request.get_json()

    sequence_id = None
    if request_json and 'sequence_id' in request_json:
        sequence_id = request_json['sequence_id']
    elif request.args and 'sequence_id' in request.args:
        sequence_id = request.args['sequence_id']

    print("Looking up observations for sequence_id={}".format(sequence_id))
    rows = get_observations(sequence_id)
    print("Found {} rows".format(len(rows)))
    response_json = dict(data=rows, count=len(rows))

    # If looking for a specific sequence then get file information
    sequence_files = defaultdict(list)
    if sequence_id:
        # Look for filename in first row
        seq_dir_in_bucket = ''
        try:
            seq_dir_in_bucket = rows[0]['file_path']
            print("Seq dir: ", seq_dir_in_bucket)
        except IndexError:
            print("No rows")

        sequence_dir = os.path.dirname(seq_dir_in_bucket)
        if sequence_dir > '':
            print("Looking for files in {}".format(sequence_dir))
            for blob in bucket.list_blobs(prefix=sequence_dir):
                filename = os.path.basename(blob.name)
                _, ext = os.path.splitext(filename)
                sequence_files[ext.replace('.', '')].append(filename)

            response_json['sequence_files'] = sequence_files
            response_json['sequence_dir'] = sequence_dir

    body = flask.json.dumps(response_json, default=json_decoder)
    headers = {
        'content-type': "application/json",
        'Access-Control-Allow-Origin': "*",
    }

    return (body, headers)


def get_observations(sequence_id=None):
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

    if sequence_id:
        select_sql = """
            SELECT
                id,
                sequence_id,
                camera_id,
                date_obs,
                file_path,
                airmass,
                center_dec,
                center_ra,
                dec_mnt,
                exp_time,
                ha_mnt,
                iso,
                moon_fraction,
                moon_separation,
                ra_mnt
            FROM images t1
            WHERE sequence_id=%s
            ORDER BY date_obs DESC
            """
    else:
        select_sql = """
            SELECT t1.*, count(t2.id) as image_count
            FROM sequences t1, images t2
            WHERE t1.id=t2.sequence_id
            GROUP BY t1.id
            ORDER BY t1.start_date DESC
            """

    rows = list()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(select_sql, (sequence_id, ))
        rows = cursor.fetchall()
        cursor.close()

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
