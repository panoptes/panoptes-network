import os
import orjson

from flask import jsonify
from google.cloud import storage
from google.cloud import pubsub

from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool

PROJECT_ID = os.getenv('POSTGRES_USER', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
PUB_TOPIC = os.getenv('PUB_TOPIC', 'image-pipeline')

publisher = pubsub.PublisherClient()
storage_client = storage.Client(project=PROJECT_ID)

bucket = storage_client.get_bucket(BUCKET_NAME)

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

pubsub_topic = f'projects/{PROJECT_ID}/topics/{PUB_TOPIC}'


# Connection pools reuse connections between invocations,
# and handle dropped or expired connections automatically.
pg_pool = None


# Entry point
def header_to_db(request):
    """Add a FITS header to the datbase.

    This endpoint looks for two parameters, `headers` and `bucket_path`. If
    `bucket_path` is present then the header information will be pull from the file
    itself. Additionally, any `headers` will be used to update the header information
    from the file. If no `bucket_path` is found then only the `headers` will be used.

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()

    header = dict()

    bucket_path = request_json.get('bucket_path')
    object_id = request_json.get('object_id')
    header = request_json.get('headers')

    if not bucket_path and not header:
        return 'No headers or bucket_path, nothing to do!'

    print(f"File: {bucket_path}")
    print(f"Header: {header!r}")

    if bucket_path:
        print("Looking up header for file: ", bucket_path)
        storage_blob = bucket.get_blob(bucket_path)
        if storage_blob:
            file_headers = lookup_fits_header(storage_blob)
            file_headers.update(header)
            file_headers['FILENAME'] = storage_blob.public_url

            if object_id is None:
                object_id = storage_blob.id
                file_headers['FILEID'] = object_id

            header.update(file_headers)
        else:
            return f"Nothing found in storage bucket for {bucket_path}"

    seq_id = header['SEQID']
    img_id = header['IMAGEID']
    print(f'Adding headers: Seq: {seq_id} Img: {img_id}')

    # Pass the parsed header information
    try:
        add_header_to_db(header)
    except Exception as e:
        success = False
        response_msg = f'Error adding header: {e!r}'
    else:
        # Send to plate-solver
        print("Forwarding to plate-solver: {}".format(bucket_path))
        data = {'sequence_id': seq_id,
                'image_id': img_id,
                'state': 'metadata_received',
                'bucket_path': str(bucket_path),
                'object_id': str(object_id)
                }
        publisher.publish(pubsub_topic, b'cf-header-to-db finished', **data)
        success = True
        response_msg = f'Header added to DB for {bucket_path}'

    return jsonify(success=success, msg=response_msg)


def add_header_to_db(header):
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
            meta_insert('units', cursor, **unit_data)

            camera_data = {
                'unit_id': unit_id,
                'id': camera_id,
            }
            meta_insert('cameras', cursor, **camera_data)

            seq_data = {
                'id': seq_id,
                'unit_id': unit_id,
                'start_date': header.get('SEQID', None).split('_')[-1],
                'exptime': header.get('EXPTIME'),
                'pocs_version': header.get('CREATOR', ''),
                'state': 'receiving_files',
                'field': header.get('FIELD', ''),
            }
            print("Inserting sequence: {}".format(seq_data))

            try:
                meta_insert('sequences', cursor, **seq_data)
            except Exception as e:
                print("Can't insert sequence: {}".format(seq_id))
                raise e

            image_data = {
                'id': img_id,
                'sequence_id': seq_id,
                'camera_id': camera_id,
                'obstime': header.get('DATE-OBS'),
                'ra_mnt': header.get('RA-MNT'),
                'ha_mnt': header.get('HA-MNT'),
                'dec_mnt': header.get('DEC-MNT'),
                'exptime': header.get('EXPTIME'),
                'file_path': header.get('FILENAME'),
                'headers': orjson.dumps(header).decode('utf-8'),
                'state': 'metadata_received'
            }

            meta_insert('images', cursor, **image_data)
            print("Header added for SEQ={} IMG={}".format(seq_id, img_id))
        except Exception as e:
            update_state('image_metadata_failed', sequence_id=seq_id, image_id=img_id)
            raise e
        finally:
            cursor.close()
            pg_pool.putconn(conn)

    return True


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
        print("Error in insert: " + e)

    return


def lookup_fits_header(remote_path):
    """Read the FITS header from storage.

    FITS Header Units are stored in blocks of 2880 bytes consisting of 36 lines
    that are 80 bytes long each. The Header Unit always ends with the single
    word 'END' on a line (not necessarily line 36).

    Here the header is streamed from Storage until the 'END' is found, with
    each line given minimal parsing.

    See https://fits.gsfc.nasa.gov/fits_primer.html for overview of FITS format.

    Args:
        remote_path (`google.cloud.storage.blob.Blob`): Blob or path to remote blob.
            If just the blob name is given then the blob is looked up first.

    Returns:
        dict: FITS header as a dictonary.
    """
    i = 1
    if remote_path.name.endswith('.fz'):
        i = 2  # We skip the compression header info

    headers = dict()

    streaming = True
    while streaming:
        # Get a header card
        start_byte = 2880 * (i - 1)
        end_byte = (2880 * i) - 1
        b_string = remote_path.download_as_string(start=start_byte, end=end_byte)

        # Loop over 80-char lines
        for j in range(0, len(b_string), 80):
            item_string = b_string[j: j + 80].decode()

            # End of FITS Header, stop streaming
            if item_string.startswith('END'):
                streaming = False
                break

            # Get key=value pairs (skip COMMENTS and HISTORY)
            if item_string.find('=') > 0:
                k, v = item_string.split('=')

                # Remove FITS comment
                if ' / ' in v:
                    v = v.split(' / ')[0]

                v = v.strip()

                # Cleanup and discover type in dumb fashion
                if v.startswith("'") and v.endswith("'"):
                    v = v.replace("'", "").strip()
                elif v.find('.') > 0:
                    v = float(v)
                elif v == 'T':
                    v = True
                elif v == 'F':
                    v = False
                else:
                    v = int(v)

                headers[k.strip()] = v

        i += 1

    return headers


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
        raise ValueError('Need either a sequence_id or an image_id')

    for table, id_col in zip(['sequences', 'images'], [sequence_id, image_id]):
        if id_col is None:
            continue

        update_sql = f"""
                    UPDATE {table}
                    SET state=%s
                    WHERE id=%s
                    """
        try:
            cursor.execute(update_sql, [state, sequence_id])
        except Exception as e:
            print(f"Error in insert (error): {e!r}")
            print(f"Error in insert (sql): {update_sql}")
            print(f"Error in insert (kwargs): {kwargs!r}")
            return False

    return True


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)
