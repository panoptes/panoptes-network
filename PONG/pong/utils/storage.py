import os
import re
import time
from warnings import warn

import google.cloud.exceptions
from google.cloud import storage

from pocs.utils.images import fits as fits_utils


def get_bucket(name):
    """Get Storage bucket object.

    Args:
        name (str): Name of Storage bucket

    Returns:
        google.cloud.storage.client.Client|None: Stroage Client or None
            if bucket does not exist.
    """
    client = storage.Client()
    bucket = None

    try:
        bucket = client.get_bucket(name)
    except google.cloud.exceptions.NotFound:
        print('Sorry, that bucket does not exist!')

    return bucket


def get_observation_blob(blob_name, bucket_name='panoptes-survey'):
    """Returns an individual Blob.

    Args:
        blob_name (str): Full name of Blob to be fetched.
        bucket_name (str, optional): Name of Storage bucket where Observation is
            stored, default `panoptes-survey` (Shouldn't need to change).

    Returns:
        google.cloud.storage.blob.Blob|None: Blob object or None.
    """
    return get_bucket(bucket_name).get_blob(blob_name)


def get_observation_blobs(prefix, include_pointing=False, bucket_name='panoptes-survey'):
    """Returns the list of Storage blobs (files) matching the prefix.

    Args:
        prefix (str): Path in storage to observation sequence, e.g.
            'PAN006/Hd189733/7bab97/20180327T071126/'.
        include_pointing (bool, optional): Whether or not to include the pointing file,
            default False.
        bucket_name (str, optional): Name of Storage bucket where Observation is
            stored, default `panoptes-survey` (Shouldn't need to change).

    Returns:
        google.cloud.storage.blob.Blob: Blob object.
    """

    # The bucket we will use to fetch our objects
    bucket = get_bucket(bucket_name)

    objs = list()
    for f in bucket.list_blobs(prefix=prefix):
        if 'pointing' in f.name and not include_pointing:
            continue
        elif f.name.endswith('.fz') is False:
            continue
        else:
            objs.append(f)

    return sorted(objs, key=lambda x: x.name)


def download_fits_file(img_blob, save_dir='.', force=False, callback=None):
    """Downloads (and uncompresses) the image blob data.

    Args:
        img_blob (str|google.cloud.storage.blob.Blob): Blob object corresponding to FITS file.
            If just the blob name is given then file will be downloaded.
        save_dir (str, optional): Path for saved file, defaults to current directory.
        force (bool, optional): Force a download even if file exists locally, default False.
        callback (callable, optional): A callable object that gets called at end of
        function.

    Returns:
        str: Path to local (uncompressed) FITS file
    """
    if isinstance(img_blob, str):
        img_blob = get_observation_blob(img_blob)

    fits_fz_fn = img_blob.name.replace('/', '_')
    fits_fz_fn = os.path.join(save_dir, fits_fz_fn)
    fits_fn = fits_fz_fn.replace('.fz', '')

    # If we don't  have file (or force=True) then download directly to
    # (compressed) FITS file.
    if not os.path.exists(fits_fn):
        with open(fits_fz_fn, 'wb') as f:
            img_blob.download_to_file(f)

    # Wait for download
    timeout = 10
    while os.path.exists(fits_fz_fn) is False:
        timeout -= 1
        if timeout < 0:
            return None
        time.sleep(1)

    # Once downloaded, uncompress
    try:
        fits_fn = fits_utils.fpack(fits_fz_fn, unpack=True)
    except Exception as e:
        warn("Can't unpack file: {}".format(fits_fz_fn))
        raise FileNotFoundError(e)

    # User supplied callback (e.g. logging)
    if callback is not None:
        try:
            callback()
        except TypeError as e:
            warn('callback must be callable')

    return fits_fn


def upload_fits_file(img_path, bucket_name='panoptes-survey'):
    """Uploads an image to the storage bucket.

    Args:
        img_blob (str|google.cloud.storage.blob.Blob): Blob object corresponding to FITS file.
            If just the blob name is given then file will be downloaded.
        save_dir (str, optional): Path for saved file, defaults to current directory.
        force (bool, optional): Force a download even if file exists locally, default False.
        callback (callable, optional): A callable object that gets called at end of
        function.

    Returns:
        str: Path to local (uncompressed) FITS file
    """
    bucket = get_bucket(bucket_name)

    # Replace anything before the unit id
    bucket_path = re.sub(r'^.*PAN', 'PAN', img_path).replace('_', '/')

    try:
        blob = bucket.blob(bucket_path)
        blob.upload_from_filename(img_path)
    except Exception as e:
        warn("Can't upload file: {}".format(e))


def get_header(img_blob, parse_line=None):
    """Read the FITS header from storage.

    FITS Header Units are stored in blocks of 2880 bytes consisting of 36 lines
    that are 80 bytes long each. The Header Unit always ends with the single
    word 'END' on a line (not necessarily line 36).

    Here the header is streamed from Storage until the 'END' is found, with
    each line given minimal parsing.

    See https://fits.gsfc.nasa.gov/fits_primer.html for overview of FITS format.

    Args:
        img_blob (google.cloud.storage.blob.Blob): Blob object corresponding to stored FITS file.
        parse_line (callable, optional): A callable function which will be passed an 80 character
            string corresponding to each line in the header.

    Returns:
        dict: FITS header as a dictonary.
    """
    i = 1
    if img_blob.name.endswith('.fz'):
        i = 2  # We skip the compression header info

    headers = dict()

    streaming = True
    while streaming:
        # Get a header card
        start_byte = 2880 * (i - 1)
        end_byte = (2880 * i) - 1
        b_string = img_blob.download_as_string(start=start_byte, end=end_byte)

        # Loop over 80-char lines
        for j in range(0, len(b_string), 80):
            item_string = b_string[j:j + 80].decode()

            # End of FITS Header, stop streaming
            if item_string.startswith('END'):
                streaming = False
                break

            # If custom parse function supplied, call that
            if parse_line is not None:
                try:
                    parse_line(item_string)
                except TypeError as e:
                    warn('parse_line must be callable')
                continue

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
