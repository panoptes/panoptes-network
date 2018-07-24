#!/usr/bin/env python3

import os
import time

from google.cloud import pubsub
from google.cloud import logging
from google.cloud.logging.handlers import CloudLoggingHandler

from astropy.io import fits

from pong.utils.storage import download_fits_file, upload_fits_file
from pong.utils.metadb import get_db_proxy_conn, add_header_to_db
from pocs.utils.images import fits as fits_utils
from pocs.utils.data import Downloader

# Instantiates a client
logging_client = logging.Client()
handler = CloudLoggingHandler(logging_client)
logging.handlers.setup_logging(handler)

# The name of the log to write to
log_name = 'upload-listener-log'
    
# Selects the log to write to
logger = logging_client.logger(log_name)


def receive_messages(project, subscription_name, topic, loop=True):
    """Receives messages from a pull subscription."""
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        project, subscription_name)

    db_conn = get_db_proxy_conn()
    if db_conn is None:
        logger.log_text("ERROR: Can't get db connection")
        return

    logger.log_text("DB connection on {}".format(db_conn))

    def callback(message):
        logger.log_text('Received message: {}'.format(message))

        attrs = dict(message.attributes)

        # Get header from Storage
        storage_blob = attrs['objectId']
        # Only work on newly placed files
        if 'overwroteGeneration' not in attrs and attrs['eventType'] == 'OBJECT_FINALIZE':

            if str(storage_blob).endswith('.fits') or str(storage_blob).endswith('.fz'):
                logger.log_text("New image file uploaded to bucket:  {}".format(storage_blob))

                # Download (and uncompress) the FITS file and get headers
                try:
                    fits_fn = download_fits_file(storage_blob, save_dir='/images')
                    logger.log_text("FITS for processing: {}".format(fits_fn))
                except Exception as e:
                    logger.log_text("Problem getting file: {}".format(e))
                    return False
                else:
                    logger.log_text("Getting header for: {}".format(fits_fn))
                    if os.path.exists(fits_fn):
                        header = fits.getheader(fits_fn)
                        logger.log_text("Got header for: {}".format(header['IMAGEID']))
                    else:
                        logger.log_text("Can't find file {}".format(fits_fn))
                        return False

                # Plate-solve the file and upload if successful
                logger.log_text("Plate solving file: {}".format(fits_fn))
                try:
                    solve_info = fits_utils.get_solve_field(fits_fn, timeout=120)
                    header['SOLVED'] = True
                    for k, v in solve_info.items():
                        try:
                            fits_k = k[0:8].upper()
                            header.set(fits_k, v)
                        except Exception as e:
                            logger.log_text("Skipping header: {}".format(e))

                except Exception as e:
                    logger.log_text("Can't solve file: {}".format(e))
                    header['SOLVED'] = False
                else:
                    # If we have solved then upload
                    try:
                        fz_fn = fits_utils.fpack(fits_fn)
                        logger.log_text(
                            "Plate-solve successful, uploading new file: {}".format(fz_fn))
                        upload_fits_file(fz_fn)
                    except Exception as e:
                        logger.log_text("Problem uploading file: {}".format(e))
                    finally:
                        try:
                            os.remove(fz_fn)
                        except FileNotFoundError:
                            pass

                # Add the header information to the metadb.
                try:
                    header['PSTATE'] = 'received'
                    header['FILEPATH'] = storage_blob
                except Exception:
                    logger.log_text("Can't add custom headers")

                try:
                    logger.log_text("Adding header information to metadb: {}".format(fits_fn))
                    img_row = add_header_to_db(header, conn=db_conn, logger=logger)
                except Exception as e:
                    logger.log_text("Error: {}".format(e))
                if img_row:
                    logger.log_text("Image {} received by metadb".format(img_row[0]))

                logger.log_text("Cleaning up {}".format(fits_fn))
                try:
                    os.remove(fits_fn)
                except FileNotFoundError as e:
                    pass

                message.ack()
        else:
            # If not new file acknowledge message
            message.ack()

        return True

    flow_control = pubsub.types.FlowControl(max_messages=10)
    subscriber.subscribe(subscription_path,
                         callback=callback,
                         flow_control=flow_control)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    logger.log_text('Listening for messages on {}'.format(subscription_path))
    while True:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            break

    logger.log_text('Stopping listener for {}'.format(subscription_path))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Listen for PubSub messages of file uploads")

    parser.add_argument('--loop', action='store_true', default=True,
                        help="If should keep reading, defaults to True")
    parser.add_argument("--project", default='panoptes-survey', help="Google Cloud project id")
    parser.add_argument('--topic', default='new-observation',
                        help='Name of the topic to subscribe to, default "new-observation"')
    parser.add_argument("--subscription", default='plate-solver',
                        help="Google Cloud project id"
                        )
    parser.add_argument(
        '--folder',
        default='/usr/share/astrometry/',
        help='Destination folder for astrometry indices.',
    )
    args = parser.parse_args()

    logger.log_text("Downloading files for plate-solving")
    try:
        dl = Downloader(data_folder=args.folder, wide_field=True, narrow_field=True)
        dl.download_all_files()
    except Exception as e:
        logger.log_text("Can't download solve files: {}".format(e))

    logger.log_text("Calling with: {} {}".format(args.project, args.subscription))
    receive_messages(args.project, args.subscription, args.topic, loop=args.loop)
