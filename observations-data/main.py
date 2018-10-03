from os import getenv
import flask

from decimal import Decimal
from datetime import datetime

from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

CONNECTION_NAME = getenv(
    'INSTANCE_CONNECTION_NAME',
    'panoptes-survey:us-central1:panoptes-meta'
)
DB_USER = getenv('POSTGRES_USER', 'panoptes')
DB_PASSWORD = getenv('POSTGRES_PASSWORD', None)
DB_NAME = getenv('POSTGRES_DATABASE', 'metadata')
pg_config = {
    'user': DB_USER,
    'password': DB_PASSWORD,
    'dbname': DB_NAME
}

# Connection pools reuse connections between invocations,
# and handle dropped or expired connections automatically.
pg_pool = None


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)


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
            SELECT *
            FROM images
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


def get_observations_data(request):
    request_json = request.get_json()

    sequence_id = None
    if request_json and 'sequence_id' in request_json:
        sequence_id = request_json['sequence_id']
    elif request.args and 'sequence_id' in request.args:
        sequence_id = request.args['sequence_id']

    print("Looking up observations for sequence_id={}".format(sequence_id))

    rows = get_observations(sequence_id)

    body = flask.json.dumps(dict(data=rows, count=len(rows)), default=json_decoder)
    headers = {
        'content-type': "application/json",
        'Access-Control-Allow-Origin': "*",
    }

    return (body, headers)
