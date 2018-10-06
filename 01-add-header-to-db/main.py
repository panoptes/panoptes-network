from os import getenv
from google.cloud import storage

from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool

from astropy.wcs import WCS

PROJECT_ID = getenv('POSTGRES_USER', 'panoptes')
BUCKET_NAME = getenv('BUCKET_NAME', 'panoptes-survey')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)

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


# Entry point
def header_to_db(request):
    """Add a FITS header to the datbase.

    This endpoint looks for two parameters, `headers` and `lookup_file`. If
    `lookup_file` is present then the header information will be pull from the file
    itself. Additionally, any `headers` will be used to update the header information
    from the file. If no `lookup_file` is found then only the `headers` will be used.

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()

    if 'lookup_file' in request_json:
        lookup_file = request_json['lookup_file']
    elif 'lookup_file' in request.args:
        lookup_file = request.args['lookup_file']

    if 'header' in request_json:
        header = request_json['header']

    if not lookup_file and not header:
        return f'No header or lookup_file, nothing to do!'

    if lookup_file:
        print("Looking up header for file: ", lookup_file)
        storage_blob = bucket.get_blob(data['name'])
        file_headers = lookup_fits_header(storage_blob)
        file_headers.update(headers)
        headers = file_headers

    unit_id = int(header['PANID'].strip().replace('PAN', ''))
    seq_id = header['SEQID'].strip()
    img_id = header['IMAGEID'].strip()
    camera_id = header['INSTRUME'].strip()
    print(f'Adding headers: Unit: {unit_id} Seq: {seq_id} Cam: {camera_id} Img: {img_id}')

    # Pass the parsed header information
    add_header_to_db(header)

    return f'Header information added to meta database.'


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

        unit_id = int(header['PANID'].replace('PAN', ''))
        seq_id = header['SEQID'].strip()
        img_id = header['IMAGEID'].strip()
        camera_id = header['INSTRUME'].strip()

        unit_data = {
            'id': unit_id,
            'name': header['OBSERVER'].strip(),
            'lat': float(header['LAT-OBS']),
            'lon': float(header['LONG-OBS']),
            'elevation': float(header['ELEV-OBS']),
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
            'start_date': header['SEQID'].split('_')[-1],
            'exp_time': header['EXPTIME'],
            'ra_rate': header['RA-RATE'],
            'field': header.get('FIELD', ''),
            'pocs_version': header['CREATOR'],
            'piaa_state': header.get('PSTATE', 'metadata_received'),
        }
        print("Inserting sequence: {}".format(seq_data))
        try:
            bl, tl, tr, br = WCS(header).calc_footprint()  # Corners
            print(f'WCS info: {bl} {tl} {tr} {br}')
            seq_data['coord_bounds'] = '(({}, {}), ({}, {}))'.format(
                bl[0], bl[1],
                tr[0], tr[1]
            )
            meta_insert('sequences', cursor, **seq_data)
            print("Sequence inserted w/ bounds: {}".format(seq_id))
        except Exception as e:
            print("Can't get bounds: {}".format(e))
            if 'coord_bounds' in seq_data:
                del seq_data['coord_bounds']
            try:
                meta_insert('sequences', cursor, **seq_data)
            except Exception as e:
                print("Can't insert sequence: {}".format(seq_id))
                raise e

        image_data = {
            'id': img_id,
            'sequence_id': seq_id,
            'date_obs': header['DATE-OBS'],
            'moon_fraction': header['MOONFRAC'],
            'moon_separation': header['MOONSEP'],
            'ra_mnt': header['RA-MNT'],
            'ha_mnt': header['HA-MNT'],
            'dec_mnt': header['DEC-MNT'],
            'airmass': header['AIRMASS'],
            'exp_time': header['EXPTIME'],
            'iso': header['ISO'],
            'camera_id': camera_id,
            'cam_temp': header['CAMTEMP'].split(' ')[0],
            'cam_colortmp': header['COLORTMP'],
            'cam_circconf': header['CIRCCONF'].split(' ')[0],
            'cam_measrggb': header['MEASRGGB'],
            'cam_red_balance': header['REDBAL'],
            'cam_blue_balance': header['BLUEBAL'],
            'file_path': header.get('FILENAME', '')
        }

        # Add plate-solved info.
        try:
            image_data['center_ra'] = header['CRVAL1']
            image_data['center_dec'] = header['CRVAL2']
        except KeyError:
            pass

        meta_insert('images', cursor, **image_data)

        cursor.close()

    pg_pool.putconn(conn)
    print("Header added for SEQ={} IMG={}".format(header['SEQID'], header['IMAGEID']))

    return


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

    insert_sql = '''INSERT INTO {} ({})
                    VALUES ({})
                    ON CONFLICT DO NOTHING RETURNING *'''.format(
        table,
        col_names_str,
        col_val_holders)

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
            item_string = b_string[j:j + 80].decode()

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


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)
