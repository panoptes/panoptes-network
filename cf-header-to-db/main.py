import os

from flask import jsonify
from google.cloud import storage
from google.cloud import firestore

try:
    db = firestore.Client()
except Exception as e:
    print(f'Error getting firestore client: {e!r}')


PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')

storage_client = storage.Client(project=PROJECT_ID)

bucket = storage_client.get_bucket(BUCKET_NAME)


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

    # Scrub all the entries
    for k, v in header.items():
        header[k] = v.strip()

    try:
        unit_id = int(header.get('PANID').replace('PAN', ''))
        seq_id = header.get('SEQID', '')
        sequence_time = header.get('SEQTIME')
        img_id = header.get('IMAGEID', '')
        img_time = img_id.split('_')[-1]
        camera_id = header.get('INSTRUME', '')

        seq_doc = db.document(f'observations/{seq_id}').get()

        if not seq_doc.exists:
            # If no sequence doc then probably no unit id. This is just to minimize
            # the number of lookups that would be required if we looked up unit_id
            # doc each time.
            unit_data = {
                'name': header.get('OBSERVER', ''),
                'location': firestore.GeoPoint(header['LAT-OBS'], header['LONG-OBS']),
                'elevation': float(header.get('ELEV-OBS')),
            }
            db.document(f'units/{unit_id}').set(unit_data, merge=True)

            seq_data = {
                'unit_id': unit_id,
                'camera_id': camera_id,
                'start_time': sequence_time,
                'exptime': header.get('EXPTIME'),
                'pocs_version': header.get('CREATOR', ''),
                'field': header.get('FIELD', ''),
                'origin': header.get('ORIGIN'),  # Project PANOPTES
                'camera_filter': header.get('FILTER'),
                'iso': header.get('ISO'),
                'status': 'receiving_files'
            }

            try:
                print("Inserting sequence: {}".format(seq_data))
                seq_doc.reference.create(seq_data)
            except Exception as e:
                print(f"Can't insert sequence {seq_id}: {e!r}")
                raise e

        image_doc = db.document(f'images/{img_id}').get()

        if not image_doc.exists:
            print("Adding header for SEQ={} IMG={}".format(seq_id, img_id))
            image_data = {
                'sequence_id': seq_id,
                'time': img_time,
                'file_path': header.get('FILENAME'),
                # Observation information
                'airmass': header.get('AIRMASS'),
                'exptime': header.get('EXPTIME'),
                # Center coordinates of image
                'crval1': header.get('CRVAL1'),
                'crval2': header.get('CRVAL2'),
                'moonfrac': header.get('MOONFRAC'),
                'moonsep': header.get('MOONSEP'),
                # Location information
                'ha_mnt': header.get('HA-MNT'),
                'ra_mnt': header.get('RA-MNT'),
                'dec_mnt': header.get('DEC-MNT'),
                # Camera properties
                'measev': header.get('MEASEV'),
                'measev2': header.get('MEASEV2'),
                'measrggb': header.get('MEASRGGB'),
                'camsn': header.get('CAMSN'),
                'camtemp': header.get('CAMTEMP'),
                'circconf': header.get('CIRCCONF'),
                'colortmp': header.get('COLORTMP'),
                'bluebal': header.get('BLUEBAL'),
                'redbal': header.get('REDBAL'),
                'whtlvln': header.get('WHTLVLN'),
                'whtlvls': header.get('WHTLVLS'),
                'status': 'received',
            }
            try:
                image_doc.reference.create(image_data)
            except Exception as e:
                print(f"Can't insert image info {img_id}: {e!r}")

    except Exception as e:
        # update_state('image_metadata_failed', sequence_id=seq_id, image_id=img_id)
        raise e

    return True


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
