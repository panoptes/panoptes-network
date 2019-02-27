import os

import requests

image_received_endpoint = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/bucket-upload'
)


def bucket_upload(data, context):
    """ Small wrapper the responds to a bucket upload and forwards to `cf-image-received` """

    bucket_path = data['name']
    print(f"Received: {bucket_path}")

    _, file_ext = os.path.splitext(bucket_path)

    if file_ext == 'fz':
        requests.post(image_received_endpoint, json={
            'bucket_path': bucket_path
        })
