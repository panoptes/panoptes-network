import os

from warnings import warn

import psycopg2


def get_db_conn(instance='panoptes-meta', db_name='panoptes', db_user='panoptes', port=5432):
    """Gets a connection to the Cloud SQL db.

    Args:
        instance (str, optional): Cloud SQL instance to connect to.
        db_user (str, optional): Name of db user.
        db_name (str, optional): Name of db.
        port (int, optional): DB port.

    Returns:
        `psycopg2.Connection`: DB connection handle.
    """
    try:
        pg_pass = os.environ['PGPASSWORD']
    except KeyError:
        warn("DB password has not been set")
        return None

    ssl_root_cert = os.path.join(os.environ['SSL_KEYS_DIR'], instance, 'server-ca.pem')
    ssl_client_cert = os.path.join(os.environ['SSL_KEYS_DIR'], instance, 'client-cert.pem')
    ssl_client_key = os.path.join(os.environ['SSL_KEYS_DIR'], instance, 'client-key.pem')

    host_lookup = {
        'panoptes-meta': os.environ['METADB_IP'],
        'tess-catalog': os.environ['TESSDB_IP'],
    }

    conn_params = {
        'sslmode': 'verify-full',
        'sslrootcert': ssl_root_cert,
        'sslcert': ssl_client_cert,
        'sslkey': ssl_client_key,
        'hostaddr': host_lookup[instance],
        'host': instance,
        'port': port,
        'user': db_user,
        'dbname': db_name,
        'password': pg_pass,
    }
    conn_str = ' '.join("{}={}".format(k, v) for k, v in conn_params.items())

    conn = psycopg2.connect(conn_str)
    return conn


def get_cursor(**kwargs):
    """Get a Cursor object.

    Args:
        **kwargs: Passed to `get_db_conn`

    Returns:
        `psycopg2.Cursor`: Cursor object.
    """
    conn = get_db_conn(**kwargs)
    cur = conn.cursor()

    return cur


def meta_insert(table, **kwargs):
    """Inserts arbitrary key/value pairs into a table.

    Args:
        table (str): Table name to be inserted.
        **kwargs: List of key/value pairs corresponding to columns in the
            table.

    Returns:
        tuple|None: Returns the inserted row or None.
    """
    conn = get_db_conn()
    cur = conn.cursor()

    col_names = ','.join(kwargs.keys())
    col_val_holders = ','.join(['%s' for _ in range(len(kwargs))])

    insert_sql = 'INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING RETURNING *'.format(
        table, col_names, col_val_holders)

    cur.execute(insert_sql, list(kwargs.values()))
    conn.commit()

    try:
        return cur.fetchone()
    except Exception as e:
        warn(e)
        return None


def add_header_to_db(header):
    """Add FITS image info to metadb.

    Note:
        This function doesn't check header for proper entries and
        assumes a large list of keywords. See source for details.

    Args:
        header (dict): FITS Header data from an observation.

    Returns:
        bool: If all header data was successfully stored.
    """
    unit_id = int(header['OBSERVER'].strip().replace('PAN', ''))
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
    meta_insert('units', **unit_data)

    camera_data = {
        'unit_id': unit_id,
        'id': camera_id,
    }
    meta_insert('cameras', **camera_data)

    seq_data = {
        'id': seq_id,
        'unit_id': unit_id,
        'start_date': header['SEQID'].split('_')[-1],
        'exp_time': header['EXPTIME'],
        'ra_rate': header['RA-RATE'],
        'pocs_version': header['CREATOR'],
    }
    meta_insert('sequences', **seq_data)

    image_data = {
        'id': img_id,
        'seq_id': seq_id,
        'obs_date': header['DATE-OBS'],
        'moon_frac': header['MOONFRAC'],
        'moon_sep': header['MOONSEP'],
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
    }

    # Add plate-solved info.
    try:
        image_data['center_ra'] = header['CRVAL1']
        image_data['center_dec'] = header['CRVAL2']
    except KeyError:
        pass

    db_img_id = meta_insert('images', **image_data)

    return db_img_id == img_id
