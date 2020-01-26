import os
import sys
import json
import base64
from contextlib import suppress

from google.cloud import storage
from google.cloud import firestore
from dateutil.parser import parse as parse_date

try:
    db = firestore.Client()
except Exception as e:
    print(f'Error getting firestore client: {e!r}')


PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')

bucket = storage.Client(project=PROJECT_ID).get_bucket(BUCKET_NAME)


def entry_point(pubsub_message, context):
    """Receive and process main request for topic.

    The arriving `pubsub_message` will be in a `PubSubMessage` format:

    https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage

    ```
        pubsub_message = {
          "data": string,
          "attributes": {
            string: string,
            ...
        }
        context = {
          "messageId": string,
          "publishTime": string
        }
    ```

    Args:
         pubsub_message (dict):  The dictionary with data specific to this type of
            pubsub_message. The `data` field contains the PubsubMessage message. The
            `attributes` field will contain custom attributes if there are any.
        context (google.cloud.functions.Context): The Cloud Functions pubsub_message
            metadata. The `event_id` field contains the Pub/Sub message ID. The
            `timestamp` field contains the publish time.
    """
    print(f'Function triggered with: {pubsub_message!r} {context!r}')

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        try:
            data = json.loads(
                base64.b64decode(pubsub_message['data']).decode())

        except Exception as e:
            msg = ('Invalid Pub/Sub message: '
                   'data property is not valid base64 encoded JSON')
            print(f'error: {e}')
            return f'Bad Request: {msg}', 400

        attributes = pubsub_message.get('attributes', dict())

        try:
            print(f'Processing: data={data!r} attributes={attributes!r}')
            process_topic(data, attributes)
            # Flush the stdout to avoid log buffering.
            sys.stdout.flush()
            return ('', 204)  # 204 is no-content success

        except Exception as e:
            print(f'error: {e}')
            return ('', 500)

    return ('', 500)


def process_topic(data, attributes=None):
    """Add a FITS header to the database.

    Args:
        data (dict): A dictionary that should contain the `bucket_path`
            corresponding to location within the storage bucket.
        attributes (dict|None, optional): Attributes from the pubsub message.

    No Longer Returned:
        dict: json status description.

    Raises:
        Exception: If anything goes wrong.
    """

    bucket_path = data.get('bucket_path')
    object_id = data.get('object_id')
    header = data.get('headers', dict())

    if not bucket_path:
        raise Exception('No bucket_path, nothing to do!')

    print("Looking up header for file: ", bucket_path)
    storage_blob = bucket.get_blob(bucket_path)
    if storage_blob:
        file_headers = lookup_fits_header(storage_blob)
        file_headers.update(header)

        # Change filename to public url of file.
        file_headers['FILENAME'] = storage_blob.public_url

        # This includes full generation information for storage
        # See https://cloud.google.com/storage/docs/object-versioning
        if object_id is None:
            object_id = storage_blob.id
            file_headers['FILEID'] = object_id

        header.update(file_headers)
    else:
        raise Exception(f"Nothing found in storage bucket for {bucket_path}")

    seq_id = header['SEQID']
    img_id = header['IMAGEID']
    print(f'Adding headers: Seq: {seq_id} Img: {img_id}')

    # Pass the parsed header information
    try:
        add_header_to_db(header, bucket_path)
    except Exception as e:
        # obj_data = None
        response_msg = f'Error adding header: {e!r}'
    else:
        # Send to plate-solver
        # print(f"Forwarding to plate-solver: {bucket_path}")
        # obj_data = {'image_id': img_id}
        # requests.post(plate_solve_endpoint, json=obj_data)

        response_msg = f'New image: sequence_id={seq_id} image_id={img_id}'

    print(response_msg)


def add_header_to_db(header, bucket_path):
    """Add FITS image info to metadb.

    Note:
        This function doesn't check header for proper entries and
        assumes a large list of keywords. See source for details.

    Args:
        header (dict): FITS Header data from an observation.
        bucket_path (str): Full path to the image in a Google Storage Bucket.

    Returns:
        str: The image_id.

    Raises:
        e: Description
    """

    # Scrub all the entries
    for k, v in header.items():
        with suppress(AttributeError):
            header[k] = v.strip()

    try:
        unit_id = header.get('PANID')
        seq_id = header.get('SEQID', '')
        sequence_time = parse_date(header.get('SEQTIME'))
        img_id = header.get('IMAGEID', '')
        img_time = parse_date(img_id.split('_')[-1])
        camera_id = header.get('INSTRUME', '')

        seq_doc = db.document(f'observations/{seq_id}').get()

        # Only process sequence if in a certain state.
        valid_status = ['metadata_received', 'receiving_files']

        if not seq_doc.exists or seq_doc.get('status') in valid_status:
            # If no sequence doc then probably no unit id. This is just to minimize
            # the number of lookups that would be required if we looked up unit_id
            # doc each time.
            unit_doc_ref = db.document(f'units/{unit_id}')

            try:
                unit_data = {
                    'name': header.get('OBSERVER', ''),
                    'location': firestore.GeoPoint(header['LAT-OBS'], header['LONG-OBS']),
                    'elevation': float(header.get('ELEV-OBS')),
                    'status': 'active'  # Assuming we are active since we received files.
                }
                unit_doc_ref.set(unit_data, merge=True)
            except Exception:
                pass

            seq_data = {
                'unit_id': unit_id,
                'camera_id': camera_id,
                'time': sequence_time,
                'exptime': header.get('EXPTIME'),
                'project': header.get('ORIGIN'),  # Project PANOPTES
                'software_version': header.get('CREATOR', ''),
                'field_name': header.get('FIELD', ''),
                'camera_filter': header.get('FILTER'),
                'iso': header.get('ISO'),
                'ra': header.get('CRVAL1'),
                'dec': header.get('CRVAL2'),
                'status': 'receiving_files',
            }

            try:
                print("Inserting sequence: {}".format(seq_data))
                seq_doc.reference.set(seq_data, merge=True)
            except Exception as e:
                print(f"Can't insert sequence {seq_id}: {e!r}")

        valid_status = ['metadata_received', 'uploaded']
        image_doc = db.document(f'images/{img_id}').get()

        image_status = image_doc.get('status')

        if not image_doc.exists or image_status in valid_status:
            print("Adding header for SEQ={} IMG={}".format(seq_id, img_id))

            measrggb = header.get('MEASRGGB').split(' ')

            image_data = {
                'sequence_id': seq_id,
                'time': img_time,
                'bucket_path': bucket_path,
                # Observation information
                'airmass': header.get('AIRMASS'),
                'exptime': header.get('EXPTIME'),
                # Center coordinates of image
                'moonfrac': header.get('MOONFRAC'),
                'moonsep': header.get('MOONSEP'),
                # Location information
                'ra_image': header.get('CRVAL1'),
                'dec_image': header.get('CRVAL2'),
                'ha_mnt': header.get('HA-MNT'),
                'ra_mnt': header.get('RA-MNT'),
                'dec_mnt': header.get('DEC-MNT'),
                # Camera properties
                'measev': header.get('MEASEV'),
                'measev2': header.get('MEASEV2'),
                'measr': int(measrggb[0]),
                'measg': int(measrggb[1]),
                'measg2': int(measrggb[2]),
                'measb': int(measrggb[3]),
                'camtemp': float(header.get('CAMTEMP').split(' ')[0]),
                'circconf': float(header.get('CIRCCONF').split(' ')[0]),
                'colortmp': header.get('COLORTMP'),
                'bluebal': header.get('BLUEBAL'),
                'redbal': header.get('REDBAL'),
                'whtlvln': header.get('WHTLVLN'),
                'whtlvls': header.get('WHTLVLS'),
                'status': 'uploaded',
            }
            try:
                image_doc.reference.set(image_data, merge=True)
            except Exception as e:
                print(f"Can't insert image info {img_id}: {e!r}")
        else:
            print(f'Image exists with status={image_status} so not updating record details')

    except Exception as e:
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
