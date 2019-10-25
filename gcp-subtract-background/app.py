import os
import sys
import tempfile

from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import storage
import google.cloud.logging

import numpy as np
from astropy.io import fits
from astropy.stats import SigmaClip
from photutils import MeanBackground
from photutils import SExtractorBackground
from photutils import MedianBackground
from photutils import MMMBackground
from photutils import BkgZoomInterpolator
from photutils import Background2D

from panoptes.utils.images import fits as fits_utils


logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

app = Flask(__name__)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')

# Storage
try:
    storage_client = storage.Client(project=PROJECT_ID)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-raw-images')
LEGACY_BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')

OUTPUT_BUCKET_NAME = os.getenv('OUTPUT_BUCKET_NAME', 'panoptes-processed-images')
BACKGROUND_BUCKET_NAME = os.getenv('BACKGROUND_BUCKET_NAME', 'panoptes-backgrounds')

estimators = {
    'sexb': SExtractorBackground,
    'median': MedianBackground,
    'mean': MeanBackground,
    'mmm': MMMBackground
}
interpolators = {
    'zoom': BkgZoomInterpolator,
}


@app.route('/', methods=['GET', 'POST'])
def main():
    """Get the latest records as JSON.

    Returns:
        TYPE: Description
    """
    print(f"Background subtraction started")
    if request.json:
        params = request.get_json(force=True)
        bucket_path = params.get('bucket_path', None)
        if bucket_path is not None:
            use_legacy = params.get('legacy', False)

            subtract_kwargs = params.get('subtract_kwargs', dict())

            with tempfile.TemporaryDirectory() as tmp_dir_name:
                print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
                try:
                    print(f'Downloading image for {bucket_path}.')
                    local_path = download_blob(bucket_path, tmp_dir_name, use_legacy=use_legacy)
                    # Want to strip field name out of legacy
                    if use_legacy:
                        print(f'Found legacy path, removing field name')
                        unit_id, field_name, cam_id, seq_id, image_name = bucket_path.split('/')
                        bucket_path = os.path.join(unit_id, cam_id, seq_id, image_name)
                        print(f'New name: {bucket_path}')
                    print(f'Subtracting background for {local_path}.')

                    uploaded_uri = subtract_color_background(local_path,
                                                             bucket_path,
                                                             **subtract_kwargs)

                    return jsonify(bucket_path=f'{OUTPUT_BUCKET_NAME}/{uploaded_uri}')
                except Exception as e:
                    print(f'Problem with subtracting background: {e!r}')
                    return jsonify(error=e)
                finally:
                    print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')
        else:
            return jsonify(error="No 'bucket_path' parameter given")


def subtract_color_background(fits_fn,
                              bucket_path,
                              box_size=(84, 84),
                              filter_size=(3, 3),
                              camera_bias=2048,
                              estimator='mean',
                              interpolator='zoom',
                              sigma=5,
                              iters=5,
                              exclude_percentile=100
                              ):
    """Get the background for each color channel.

    Most of the options are described in the `photutils.Background2D` page:

    https://photutils.readthedocs.io/en/stable/background.html#d-background-and-noise-estimation

    Args:
        fits_fn (str): The filename of the FITS image.
        bucket_path (None, optional): Bucket path for upload, no upload if None (default).
        box_size (tuple, optional): The box size over which to compute the
            2D-Background, default (84, 84).
        filter_size (tuple, optional): The filter size for determining the median,
            default (3, 3).
        camera_bias (int, optional): The built-in camera bias, default 2048.
        estimator (str, optional): The estimator object to use, default 'median'.
        interpolator (str, optional): The interpolater object to user, default 'zoom'.
        sigma (int, optional): The sigma on which to filter values, default 5.
        iters (int, optional): The number of iterations to sigma filter, default 5.
        exclude_percentile (int, optional): The percentage of the data (per channel)
            that can be masked, default 100 (i.e. all).

    Returns:
        list: A list containing a `photutils.Background2D` for each color channel, in RGB order.
    """

    print(f"Performing background subtraction for {fits_fn}")
    print(f"{estimator} {interpolator} {box_size} Sigma: {sigma} Iter: {iters}")

    bkg_estimator = estimators[estimator]()
    interp = interpolators[interpolator]()

    data = fits.getdata(fits_fn)
    header = fits_utils.getheader(fits_fn)

    # Get the data per color channel.
    rgb_data = get_color_data(data)

    backgrounds = list()
    for color, color_data in zip(['R', 'G', 'B'], rgb_data):
        print(f'Performing background {color} for {fits_fn}')

        bkg = Background2D(color_data,
                           box_size,
                           filter_size=filter_size,
                           sigma_clip=SigmaClip(sigma=sigma, maxiters=iters),
                           bkg_estimator=bkg_estimator,
                           exclude_percentile=exclude_percentile,
                           mask=color_data.mask,
                           interpolator=interp)

        # Create a masked array for the background
        backgrounds.append(np.ma.array(data=bkg.background, mask=color_data.mask))
        print(f"{color} Value: {bkg.background_median:.02f} RMS: {bkg.background_rms_median:.02f}")

    # Create one array for the backgrounds, where any holes are filled with zeros.
    # Add bias back to data so we can save with unsigned.
    full_background = np.ma.array(backgrounds).sum(0).filled(0)

    # Make FITS file with background subtracted version
    upload_background(fits_fn, bucket_path, full_background, header)

    # Subtract the background but add bias so we can save unsigned
    subtacted_data = data - full_background + camera_bias

    # Replace FITS file with subtracted version
    try:
        header['BKGSUB'] = True
        hdu = fits.PrimaryHDU(data=subtacted_data.astype(np.uint16), header=header)
        hdu.writeto(fits_fn, overwrite=True)
        # Pack the background
        fits_fz_fn = fits_utils.fpack(fits_fn)
        print(f'FITS file saved to {fits_fz_fn}')
    except Exception as e:
        print(f'Error writing substracted FITS: {e}')

    print(f'Uploading {fits_fz_fn} to {OUTPUT_BUCKET_NAME}/{bucket_path}')
    # Upload with folder structure
    uploaded_uri = upload_blob(fits_fn, bucket_path)

    return uploaded_uri


def get_color_data(data):
    """Split the data according to the RGB Bayer pattern.

    Args:
        data (`numpy.array`): The image data.

    Returns:
        list: A list contained an `numpy.ma.array` for each color channel.
    """
    red_pixels_mask = np.ones_like(data)
    green_pixels_mask = np.ones_like(data)
    blue_pixels_mask = np.ones_like(data)

    red_pixels_mask[1::2, 0::2] = False  # Red
    green_pixels_mask[1::2, 1::2] = False  # Green
    green_pixels_mask[0::2, 0::2] = False  # Green
    blue_pixels_mask[0::2, 1::2] = False  # Blue

    red_data = np.ma.array(data, mask=red_pixels_mask)
    green_data = np.ma.array(data, mask=green_pixels_mask)
    blue_data = np.ma.array(data, mask=blue_pixels_mask)

    rgb_data = [
        red_data,
        green_data,
        blue_data
    ]

    return rgb_data


def upload_background(fits_fn, bucket_path, data, header):
    # Upload background file
    try:
        back_fn = fits_fn.replace('.fits.fz', '-background.fits')
        bucket_path = bucket_path.replace('.fits.fz', '-background.fits.fz')

        header['BACKGRND'] = True

        hdu = fits.PrimaryHDU(data=data.astype(np.uint16), header=header)
        hdu.writeto(back_fn, overwrite=True)

        # Pack the background
        back_fz_fn = fits_utils.fpack(back_fn)
        print(f'Background FITS file saved to {back_fz_fn}')

        background_uri = upload_blob(back_fz_fn, bucket_path, bucket_name=BACKGROUND_BUCKET_NAME)
        print(f'Background uploaded to {background_uri}')
    except Exception as e:
        print(f'Error uploading background file for {fits_fn}: {e}')


def download_blob(bucket_path, dir_name, use_legacy=False):
    """Downloads a blob from the bucket."""
    if use_legacy:
        bucket = LEGACY_BUCKET_NAME
    else:
        bucket = BUCKET_NAME

    bucket_uri = f'gs://{bucket}/{bucket_path}'
    local_path = os.path.join(dir_name, bucket_path.replace('/', '_'))

    print(f'Downloading {bucket_uri} to {local_path}')

    with open(local_path, 'wb') as f:
        storage_client.download_blob_to_file(bucket_uri, f)

    return local_path


def upload_blob(source_file_name, destination, bucket_name=OUTPUT_BUCKET_NAME):
    """Uploads a file to the bucket."""
    print('Uploading {} to {}.'.format(source_file_name, destination))

    bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination))

    return destination


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
