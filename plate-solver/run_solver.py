#!/usr/bin/env python

import os

from google.cloud import google_logging
from google.cloud import pubsub

from pocs.utils.images import fits as fits_utils
from piaa.utils import helpers


def main(project_id=None, subscription_name=None, topic=None, *args, **kwargs):
    assert project_id is not None
    assert subscription_name is not None
    assert topic is not None

    subscriber = pubsub.SubscriberClient()

    topic = 'projects/{project_id}/topics/{topic}'.format(
        project_id=project_id,
        topic=topic,
    )
    subscription = 'projects/{project_id}/subscriptions/{sub}'.format(
        project_id=project_id,
        sub=subscription_name,
    )
    logging.info("Creating subscription")
    logging.info("Subscription: {}".format(subscription_name))
    logging.info("Topic: {}".format(topic))
    subscriber.create_subscription(subscription, topic)

    def callback(message):
        attrs = dict(message.attributes)

        event_type = attrs['eventType']
        object_id = attrs['objectId']

        if event_type is 'OBJECT_FINALIZE':
            # Get blob from storage
            blobs = helpers.get_observation_blobs(key=object_id)
            fits_fn = helpers.unpack_blob(blobs[0])
            # Plate-solve
            fits_utils.get_solve_field(fits_fn)
            # Save metadata to db

            # Compress
            fz_fn = fits_utils.fpack(fits_fn)

            # Upload solved image to storage
            helpers.upload_to_bucket(fz_fn)

        message.ack()

    future = subscriber.subscribe(subscription, callback)

    # Block
    try:
        future.result()
    except Exception as ex:
        subscription.close()
        raise


if __name__ == '__main__':
    # Instantiates a client
    logging_client = google_logging.Client()
    logging_client.setup_logging()

    import logging

    project_id = 'panoptes-survey'
    subscription_name = 'plate-solver'
    topic = 'new-observation'

    import argparse

    parser = argparse.ArgumentParser(description="Solves files upload to storage bucket")
    parser.add_argument('--project_id', default='panoptes-survey',
                        help='Google project id, default "panoptes-survey"')
    parser.add_argument('--subscription', default='plate-solver',
                        help='Name of the subscription to be created, default "plate-solver"')
    parser.add_argument('--topic', default='new-observation',
                        help='Name of the topic to subscribe to, default "new-observation"')
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='Verbose')

    os.makedirs('/var/panoptes/fits_files', exist_ok=True)

    args = parser.parse_args()

    main(**vars(args))
