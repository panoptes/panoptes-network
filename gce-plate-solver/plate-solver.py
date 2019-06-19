#!/usr/bin/env python

import os
import sys
import time
import tempfile

from google.cloud import storage
from google.cloud import pubsub
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler

import csv
import requests
from dateutil.parser import parse as parse_date
import numpy as np
from astropy.io import fits
from astropy.stats import SigmaClip

from photutils import Background2D
from photutils import MeanBackground
from photutils import MMMBackground
from photutils import MedianBackground
from photutils import SExtractorBackground
from photutils import BkgZoomInterpolator

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.google.cloudsql import get_cursor
from panoptes.utils import bayer
from panoptes.piaa.utils.sources import lookup_point_sources


if ((os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '') == '') and
        (os.environ.get('GOOGLE_COMPUTE_INSTANCE', '') == '')):
    print(f"Don't know how to authenticate, refusing to run.")
    sys.exit(1)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

# Storage
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_NAME)

PUBSUB_SUB_PATH = os.getenv('SUB_PATH', 'gce-plate-solver')
subscriber_client = pubsub.SubscriberClient()
pubsub_sub_path = f'projects/{PROJECT_ID}/subscriptions/{PUBSUB_SUB_PATH}'

update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)

get_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/get-state'
)

# Maximum number of simultaneous messages to process
MAX_MESSAGES = os.getenv('MAX_MESSAGES', 2)


def main():
    print(f"Starting pubsub listen on {pubsub_sub_path}")

    try:
        # max_messages means we only process one at a time.
        flow_control = pubsub.types.FlowControl(max_messages=MAX_MESSAGES)
        scheduler = ThreadScheduler()
        future = subscriber_client.subscribe(
            pubsub_sub_path,
            callback=msg_callback,
            flow_control=flow_control,
            scheduler=scheduler
        )

        # Keeps main thread from exiting.
        print(f"Plate-solver subscriber started, entering listen loop")
        while True:
            time.sleep(30)
    except Exception as e:
        print(f'Problem in message callback: {e!r}')
        future.cancel()
        subscriber_client.close()


def msg_callback(message):

    attributes = message.attributes
    bucket_path = attributes['bucket_path']
    object_id = attributes['object_id']
    subtract_background = attributes.get('subtract_background', True)
    force = attributes.get('force_new', False)

    if force:
        print(f'Found force=True, forcing new plate solving')

    try:
        # Get DB cursors
        catalog_db_cursor = get_cursor(port=5433, db_name='v702', db_user='panoptes')
        metadata_db_cursor = get_cursor(port=5432, db_name='metadata', db_user='panoptes')
    except Exception as e:
        message.nack()
        error_msg = f"Can't connect to Cloud SQL proxy: {e!r}"
        print(error_msg)
        raise Exception(error_msg)

    print(f'Creating temporary directory for {bucket_path}')
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
        print(f'Solving {bucket_path}')
        try:
            solve_file(bucket_path,
                       object_id,
                       catalog_db_cursor,
                       metadata_db_cursor,
                       subtract_background=subtract_background,
                       force=force,
                       tmp_dir=tmp_dir_name
                       )
            print(f'Finished processing {bucket_path}.')
        except Exception as e:
            print(f'Problem with solve file: {e!r}')
            raise Exception(f'Problem with solve file: {e!r}')
        finally:
            catalog_db_cursor.close()
            metadata_db_cursor.close()
            # Acknowledge message
            print(f'Acknowledging message {message.ack_id}')
            message.ack()

            print(f'Cleaning up temporary directory: {tmp_dir_name} for {bucket_path}')


def solve_file(bucket_path,
               object_id,
               catalog_db_cursor,
               metadata_db_cursor,
               subtract_background=True,
               force=False,
               tmp_dir='/tmp'):
    try:
        unit_id, field, cam_id, seq_time, file = bucket_path.split('/')
        img_time = file.split('.')[0]
        image_id = f'{unit_id}_{cam_id}_{img_time}'
    except Exception as e:
        raise Exception(f'Invalid file, skipping {bucket_path}: {e!r}')

    # Don't process pointing images.
    if 'pointing' in bucket_path:
        print(f'Skipping pointing file: {image_id}')
        update_state('skipped', image_id=image_id)
        return

    # Don't process files that have been processed.
    if (force is False) and (get_state(image_id=image_id) == 'sources_extracted'):
        print(f'Skipping already processed image: {image_id}')
        return

    try:  # Wrap everything so we can do file cleanup
        # Download file blob from bucket
        print(f'Downloading {bucket_path}')
        fz_fn = download_blob(bucket_path, destination=tmp_dir, bucket=bucket)

        # Unpack the FITS file
        print(f'Unpacking {fz_fn}')
        try:
            fits_fn = fits_utils.funpack(fz_fn)
            if not os.path.exists(fits_fn):
                raise FileNotFoundError(f"No {fits_fn} after unpacking")
        except Exception as e:
            update_state('error_unpacking', image_id=image_id)
            raise Exception(f'Problem unpacking {fz_fn}: {e!r}')

        # Check for existing WCS info
        print(f'Getting existing WCS for {fits_fn}')
        wcs_info = fits_utils.get_wcsinfo(fits_fn)
        already_solved = len(wcs_info) > 1

        try:
            background_subtracted = fits_utils.getval(fits_fn, 'BKGSUB')
        except KeyError:
            background_subtracted = False

        # Do background subtraction
        if subtract_background and background_subtracted is False:
            fits_fn = subtract_color_background(fits_fn, bucket_path)

        # Solve fits file
        if not already_solved or force:
            print(f'Plate-solving {fits_fn}')
            try:
                solve_info = fits_utils.get_solve_field(fits_fn,
                                                        skip_solved=False,
                                                        overwrite=True,
                                                        timeout=90)
                print(f'Solved {fits_fn}')
            except Exception as e:
                print(f'File not solved, skipping: {fits_fn} {e!r}')
                update_state('error_solving', image_id=image_id)
                return None
        else:
            print(f'Found existing WCS for {fz_fn}')
            solve_info = None

        # Lookup point sources
        try:
            print(f'Looking up sources for {fits_fn}')
            point_sources = lookup_point_sources(
                fits_fn,
                force_new=True,
                cursor=catalog_db_cursor
            )

            # Adjust some of the header items
            point_sources['bucket_path'] = bucket_path
            point_sources['image_id'] = image_id
            point_sources['seq_time'] = seq_time
            point_sources['img_time'] = img_time
            point_sources['unit_id'] = unit_id
            point_sources['camera_id'] = cam_id
            print(f'Sources detected: {len(point_sources)} {fz_fn}')
            update_state('sources_detected', image_id=image_id)
        except Exception as e:
            print(f'FError in detection: {fits_fn} {e!r}')
            update_state('error_sources_detection', image_id=image_id)
            raise e

        print(f'Looking up sources for {fits_fn}')
        get_sources(point_sources, fits_fn, tmp_dir=tmp_dir)
        update_state('sources_extracted', image_id=image_id)

        # Upload solved file if newly solved (i.e. nothing besides filename in wcs_info)
        if solve_info is not None and (force is True or len(wcs_info) == 1):
            fz_fn = fits_utils.fpack(fits_fn)
            upload_blob(fz_fn, bucket_path, bucket=bucket)

        return

    except Exception as e:
        print(f'Error while solving field: {e!r}')
        update_state('sources_extracted', image_id=image_id)
        return False
    finally:
        print(f'Solve and extraction complete, cleaning up for {bucket_path}')

    return None


def subtract_color_background(fits_fn,
                              bucket_path=None,
                              box_size=(84, 84),
                              filter_size=(3, 3),
                              camera_bias=2048,
                              estimator='median',
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
    estimators = {
        'sexb': SExtractorBackground,
        'median': MedianBackground,
        'mean': MeanBackground,
        'mmm': MMMBackground
    }
    interpolators = {
        'zoom': BkgZoomInterpolator(),
    }

    print(f"Performing background subtraction for {fits_fn}")
    print(f"Est: {estimator} Interp: {interpolator} Box: {box_size} Sigma: {sigma} Iters: {iters}")

    data = fits.getdata(fits_fn)  # - camera_bias
    header = fits_utils.getheader(fits_fn)

    # Got the data per color channel.
    rgb_data = get_color_data(data)

    bkg_estimator = estimators[estimator]()
    interp = interpolators[interpolator]
    sigma_clip = SigmaClip(sigma=sigma, maxiters=iters)

    backgrounds = list()
    for color, color_data in zip(['R', 'G', 'B'], rgb_data):
        print(f'Performing background {color} for {fits_fn}')

        bkg = Background2D(color_data, box_size, filter_size=filter_size,
                           sigma_clip=sigma_clip, bkg_estimator=bkg_estimator,
                           exclude_percentile=exclude_percentile,
                           mask=color_data.mask,
                           interpolator=interp)

        # Create a masked array for the background
        backgrounds.append(np.ma.array(data=bkg.background, mask=color_data.mask))
        print(f"{color} Value: {bkg.background_median:.02f} RMS: {bkg.background_rms_median:.02f}")

    # Create one array for the backgrounds, where any holes are filled with the bias.
    full_background = np.ma.array(backgrounds).sum(0).filled(camera_bias)

    # Upload background file
    if bucket_path is not None:
        try:
            back_fn = fits_fn.replace('.fits', '-background.fits')
            bucket_path = bucket_path.replace('.fits', '-background.fits')

            # Make FITS file with background substracted version
            hdu = fits.PrimaryHDU(data=full_background.astype(np.int16), header=header)
            hdu.writeto(back_fn, overwrite=True)

            # Pack the background
            back_fz_fn = fits_utils.fpack(back_fn)

            # Store the background
            upload_blob(back_fz_fn, bucket_path, bucket=bucket)
        except Exception as e:
            print(f'Error uploading background file for {fits_fn}: {e}')

    # Subtract the background
    subtacted_data = data - full_background

    # Replace FITS file with subtracted version
    try:
        header['BKGSUB'] = True
        hdu = fits.PrimaryHDU(data=subtacted_data.astype(np.int16), header=header)
        hdu.writeto(fits_fn, overwrite=True)
    except Exception as e:
        print(f'Error writing substracted FITS: {e}')

    return fits_fn


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


def get_sources(point_sources, fits_fn, stamp_size=10, tmp_dir='/tmp'):
    """Get postage stamps for each PICID in the given file.

    Args:
        point_sources (`pandas.DataFrame`): A DataFrame containing the results from `sextractor`.
        fits_fn (str): The name of the FITS file to extract stamps from.
        stamp_size (int, optional): The size of the stamp to extract, default 10 pixels.
    """
    data = fits.getdata(fits_fn)
    header = fits.getheader(fits_fn)
    image_id = None

    print(f'Extracting {len(point_sources)} point sources from {fits_fn}')

    row = point_sources.iloc[0]
    sources_csv_fn = os.path.join(
        tmp_dir, f'{row.unit_id}-{row.camera_id}-{row.seq_time}-{row.img_time}.csv')
    print(f'Sources metadata will be extracted to {sources_csv_fn}')

    print(f'Starting source extraction for {fits_fn}')
    with open(sources_csv_fn, 'w') as metadata_fn:
        writer = csv.writer(metadata_fn, quoting=csv.QUOTE_MINIMAL)

        # Write out headers.
        csv_headers = [
            'picid',
            'unit_id',
            'camera_id',
            'sequence_time',
            'image_time',
            'x', 'y',
            'ra', 'dec',
            'sextractor_flags',
            'sextractor_background',
            'slice_y',
            'slice_x',
            'exptime',
            'field',
            'bucket_path',
        ]
        csv_headers.extend([f'pixel_{i:02d}' for i in range(stamp_size**2)])
        writer.writerow(csv_headers)

        for picid, row in point_sources.iterrows():
            # Get the stamp for the target
            target_slice = bayer.get_stamp_slice(
                row.x, row.y,
                stamp_size=(stamp_size, stamp_size),
                ignore_superpixel=False,
                verbose=False
            )

            # Add the target slice to metadata to preserve original location.
            row['target_slice'] = target_slice
            stamp = data[target_slice].flatten().tolist()

            row_values = [
                int(picid),
                str(row.unit_id),
                str(row.camera_id),
                parse_date(row.seq_time),
                parse_date(row.img_time),
                int(row.x), int(row.y),
                row.ra, row.dec,
                int(row['flags']),
                row.background,
                target_slice[0],
                target_slice[1],
                header.get('EXPTIME', -1),
                header.get('FIELD', 'UNKNOWN'),
                row.bucket_path,
                *stamp
            ]

            # Write out stamp data
            writer.writerow(row_values)

    # Upload the CSV files.
    try:
        upload_blob(sources_csv_fn,
                    destination=os.path.basename(sources_csv_fn).replace('-', '/'),
                    bucket_name='panoptes-detected-sources')
    except Exception as e:
        print(f'Uploading of sources failed for {sources_csv_fn}: {e!r}')
        update_state('error_uploading_sources', image_id=image_id)
    finally:
        print(f'Cleaning up after source matching {image_id}')

    return True


def download_blob(source_blob_name, destination=None, bucket=None, bucket_name='panoptes-survey'):
    """Downloads a blob from the bucket."""
    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(source_blob_name)

    # If no name then place in current directory
    if destination is None:
        destination = source_blob_name.replace('/', '_')

    if os.path.isdir(destination):
        destination = os.path.join(destination, source_blob_name.replace('/', '_'))

    blob.download_to_filename(destination)

    print('Blob {} downloaded to {}.'.format(source_blob_name, destination))

    return destination


def upload_blob(source_file_name, destination, bucket=None, bucket_name='panoptes-survey'):
    """Uploads a file to the bucket."""
    print('Uploading {} to {}.'.format(source_file_name, destination))

    if bucket is None:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination))

    return destination


def update_state(state, sequence_id=None, image_id=None):
    """Update the state of the current image or sequence."""
    requests.post(update_state_url, json={'sequence_id': sequence_id,
                                          'image_id': image_id,
                                          'state': state
                                          })

    return True


def get_state(sequence_id=None, image_id=None):
    """Gets the state of the current image or sequence."""
    res = requests.post(get_state_url, json={'sequence_id': sequence_id,
                                             'image_id': image_id,
                                             })

    if res.ok:
        return res.json()['data']['state']

    return None


if __name__ == '__main__':
    main()
