import os
import re
import requests

from flask import jsonify
from google.cloud import pubsub

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')

publisher = pubsub.PublisherClient()
PUB_TOPIC = os.getenv('PUB_TOPIC', 'find-similar-sources')
pubsub_topic = f'projects/{PROJECT_ID}/topics/{PUB_TOPIC}'

update_state_url = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/update-state'
)


def observation_psc_created(data, context):
    """ Triggered when a new PSC file is uploaded for an observation.

    The Observation PSC is created by the `df-make-observation-pc` job, which will
    upload a CSV file to the `panoptes-observation-psc` bucket. This CF will listen
    to that bucket and process new files:
        1. Update the `metadata.sequences` table with the RA/Dec boundaries for
        the sequence.
        2. Send a PubSub message to the `find-similar-sources` topic to trigger
        creation of the similar sources.

    """

    object_id = data['id']

    matches = re.match('panoptes-observation-psc/(PAN.{3}[/_].*[/_]20.{6}T.{6}).csv/*', object_id)
    if matches is not None:
        sequence_id = matches.group(1)
        print(f'Found sequence_id {sequence_id}')
    else:
        msg = f"Cannot find matching sequence_id in {object_id}"
        print(msg)
        return jsonify(success=False, msg=msg)

    # Update state
    state = 'observation_psc_created'
    print(f'Updating state for {sequence_id} to {state}')
    requests.post(update_state_url, json={'sequence_id': sequence_id, 'state': state})

    publisher.publish(pubsub_topic,
                      b'cf-observation-psc-created finished',
                      sequence_id=sequence_id)

    return jsonify(success=True, msg="Received file: {object_id}")
