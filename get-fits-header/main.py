
import os
from contextlib import suppress

from flask import jsonify
from google.cloud import storage


PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')


# Entry point
def entry_point(request):
    """Return the FITS header from a file.

    This endpoint looks for one parameters, `bucket_path`. If `bucket_path` 
    is present then the header information will be pulled from the file
    and returned as a json document.

     Note that the headers are streamed from the bucket rather than pulling
     the entire file from the bucket and then looking up the headers.

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        json_response (str): The response as json
    """
    success = False
    request_json = request.get_json()
    print(f"Received: {request_json!r}")

    if not request_json:
        return jsonify(success=success, msg=f'No request received.')

    bucket_name = request_json.get('bucket_name', BUCKET_NAME)
    bucket_path = request_json.get('bucket_path')
    bucket = storage.Client(project=PROJECT_ID).get_bucket(bucket_name)

    if not bucket_path:
        return jsonify(success=success, msg='No bucket_path, nothing to do!')

    fits_headers = dict()

    print("Looking up header for file: ", bucket_path)
    storage_blob = bucket.get_blob(bucket_path)
    if storage_blob:
        fits_headers = lookup_fits_header(storage_blob)

        # Change filename to public url of file.
        fits_headers['FILENAME'] = storage_blob.public_url
        success = True
    else:
        return jsonify(success=success, msg=f"Nothing found in storage bucket for {bucket_path}")

    return jsonify(success=success, header=fits_headers)


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
        b_string = remote_path.download_as_string(start=start_byte,
                                                  end=end_byte)

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
