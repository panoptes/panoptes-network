import os

from flask import jsonify

from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool

PROJECT_ID = os.getenv('POSTGRES_USER', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')

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


# Entry point
def get_state(request):
    """Get the sequence or image state.

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()

    sequence_id = request_json.get('sequence_id')
    image_id = request_json.get('image_id')

    if sequence_id is None and image_id is None:
        return jsonify(success=False, msg='Need either a sequence_id or an image_id')

    table = 'sequences'
    id_field = sequence_id
    if sequence_id is None:
        table = 'images'
        id_field = image_id

    id_field = id_field.replace('/', '_')

    try:
        state = get_state_call(table, id_field)
        print(f'Received {state!r}')
    except Exception as e:
        return jsonify(success=False, msg=f'Failed to update state: {e!r}')

    return jsonify(success=True,
                   msg=f'Updated {id_field} to {state}',
                   data={'state': state})


def get_state_call(table, id_field):
    """Looks up the `state` column for given table.

    Args:
        table (str): Table in which to insert.

    Returns:
        tuple|None: Returns the inserted row or None.
    """
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
        update_sql = f"SELECT state FROM {table} WHERE id=%s"
        try:
            cursor.execute(update_sql, [id_field])
            row = cursor.fetchone()
            return row[0]
        except Exception as e:
            print(f"Error in insert (error): {e!r}")
            print(f"Error in insert (sql): {update_sql}")
            return None
        finally:
            cursor.close()
            pg_pool.putconn(conn)

    return None


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)
