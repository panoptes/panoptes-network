import os
import rawpy
from copy import copy
from contextlib import suppress

from flask import jsonify
from google.cloud import storage

from astropy.io import fits

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')
UPLOAD_BUCKET = os.getenv('UPLOAD_BUCKET', 'panoptes-processed-images')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)

TMP_DIR = '/tmp'

DEFAULT_RAWPY_OPTIONS = {
    "demosaic_algorithm": rawpy.DemosaicAlgorithm.AAHD,
    "no_auto_bright": True,
    "output_bps": 16,  # 16 bit
    "half_size": True,
    "gamma": (1, 1),  # Linear
}


def make_rgb_fits(request):
    """Responds to any HTTP request.

    Notes:
        rawpy params: https://letmaik.github.io/rawpy/api/rawpy.Params.html
        rawpy enums: https://letmaik.github.io/rawpy/api/enums.html

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    if request.args and 'cr2_file' in request.args:
        raw_file = request.args.get('cr2_file')
    elif request_json and 'cr2_file' in request_json:
        raw_file = request_json['cr2_file']
    else:
        return f'No file requested'

    # Get default rawpy options
    rawpy_options = copy(DEFAULT_RAWPY_OPTIONS)
    # Update rawpy options with those passed by user
    with suppress(KeyError):
        rawpy_options.update(request_json['rawpy_options'])

    print(f'Using rawpy options')
    print(f'{rawpy_options}')

    fits_file = raw_file.replace('.cr2', '.fits.fz')

    print(f'CR2 File: {raw_file}')
    print(f'FITS File: {fits_file}')

    # Download the file locally
    base_dir = os.path.dirname(raw_file)
    base_fn = os.path.basename(raw_file)
    base_name, ext = os.path.splitext(base_fn)

    print('Getting CR2 file')
    cr2_storage_blob = bucket.get_blob(raw_file)
    tmp_fn = os.path.join(TMP_DIR, base_fn)
    print(f'Downloading to {tmp_fn}')
    cr2_storage_blob.download_to_filename(tmp_fn)

    # local_fits_file = cr2_storage_blob.download_to_filename(base_fn.replace('.cr2', '.fits.fz')

    # Read in with rawpy
    print(f'Opening via rawpy')
    try:
        with rawpy.imread(tmp_fn) as raw:
            d0 = raw.postprocess(**rawpy_options)
            print(f'Got raw data: {d0.shape}')

            # header = fits.getheader(raw_file.replace('.cr2', '.fits))
            print(f'Looping through the colors')
            for color, i in zip('rgb', range(3)):
                c0 = d0[:, :, i]
                hdul = fits.PrimaryHDU(data=c0)

                fn_out = f'{base_name}_{color}.fits'
                fn_path = os.path.join(TMP_DIR, fn_out)

                print(f'Writing {fn_out}')
                hdul.writeto(fn_path, overwrite=True)

                # Upload
                print(f"Sending {fn_out} to temp bucket")
                try:
                    bucket_fn = os.path.join(base_dir, fn_out)
                    upload_blob(fn_path, bucket_fn)
                finally:
                    print(f'Removing {fn_out}')
                    os.remove(fn_path)
    finally:
        print(f'Removing {tmp_fn}')
        os.remove(tmp_fn)

    return jsonify(success=True, msg=f"RGB FITS files made for {raw_file}")


def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = client.get_bucket(UPLOAD_BUCKET)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))
