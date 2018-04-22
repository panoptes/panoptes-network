#!/usr/bin/env python3

from warnings import warn
import time

from google.cloud import pubsub

from astropy.wcs import WCS

from pong.utils.storage import get_header, get_observation_blobs


def receive_messages(project, subscription_name, loop=True):
    """Receives messages from a pull subscription."""
    subscriber = pubsub.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        project, subscription_name)

    def callback(message):
        print('Received message: {}'.format(message))

        attrs = dict(message.attributes)

        # Get header from Storage
        storage_blob = attrs['objectId']

        # Store header in meta db
        header = get_header(storage_blob)
        wcs = WCS(header)

        # Check for plate-solve and start job if needed
        if wcs.is_celestial() is False:
            pass

        # Accept the change message
        message.ack()

    subscription = subscriber.subscribe(subscription_path)
    future = subscription.open(callback)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    print('Listening for messages on {}'.format(subscription_path))
    while loop:
        try:
            future.result()
        except Exception as e:
            warn(e)
            subscription.close()
            break
        else:
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
