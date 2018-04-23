#!/usr/bin/env python3

import time

from google.cloud import pubsub
from google.cloud import logging
from google.cloud.logging.handlers import CloudLoggingHandler

from pong.utils.storage import get_header
from pong.utils.metadb import add_header_to_db

# Instantiates a client
logging_client = logging.Client()
handler = CloudLoggingHandler(logging_client)
logging.handlers.setup_logging(handler)

# The name of the log to write to
log_name = 'upload-listener-log'

# Selects the log to write to
logger = logging_client.logger(log_name)


def receive_messages(project, subscription_name, loop=True):
    """Receives messages from a pull subscription."""
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        project, subscription_name)

    def callback(message):
        logger.log_text('Received message: {}'.format(message))

        attrs = dict(message.attributes)

        # Get header from Storage
        storage_blob = attrs['objectId']
        logger.log_text("Blob notification for  {}".format(storage_blob))

        if str(storage_blob).endswith('.fits') or str(storage_blob).endswith('.fz'):
            logger.log_text("Processing as FITS observation")

            # Store header in meta db
            try:
                header = get_header(storage_blob)
                logger.log_text("Header for {}".format(header['IMGID']))
            except Exception as e:
                logger.error("Problem getting header: {}".format(e))

            header['piaa_state'] = 'received'
            try:
                logger.log_text("Adding header information to metadb")
                img_id = add_header_to_db(header)
            except Exception as e:
                logger.log_text("Error: {}".format(e))
                logger.error(e)
            if img_id:
                logger.log_text("Image {} received by metadb".format(img_id))

                # Accept the change message
                logger.log_text("Acknowledging message {}".format(message.insertId))
                message.ack()

        return True

    flow_control = pubsub.types.FlowControl(max_messages=10)
    subscription = subscriber.subscribe(subscription_path,
                                        callback=callback,
                                        flow_control=flow_control)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    logger.log_text('Listening for messages on {}'.format(subscription_path))
    while loop:
        time.sleep(60)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Listen for PubSub messages of file uploads")

    parser.add_argument('--loop', action='store_true', default=True,
                        help="If should keep reading, defaults to True")
    parser.add_argument("--project", default='panoptes-survey', help="Google Cloud project id")
    parser.add_argument("--subscription",
                        default='new-image-listener',
                        help="Google Cloud project id"
                        )
    args = parser.parse_args()

    print("Calling with: {} {}".format(args.project, args.subscription))
    receive_messages(args.project, args.subscription, loop=args.loop)
