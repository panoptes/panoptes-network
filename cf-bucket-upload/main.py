import os

from Flask import jsonify
import requests

image_received_endpoint = os.getenv(
    'HEADER_ENDPOINT',
    'https://us-central1-panoptes-survey.cloudfunctions.net/image-received'
)

ALLOWED_EXTENSTIONS = ['.cr2', '.fits', '.fz']


def bucket_upload(data, context):
    """ Small wrapper the responds to a bucket upload and forwards to `cf-image-received` """

    bucket_path = data['name']
    object_id = data['id']

    _, file_ext = os.path.splitext(bucket_path)

    if file_ext in ALLOWED_EXTENSTIONS:
        print(f"Forwarding image file to cf-image-received")
        requests.post(image_received_endpoint, json={
            'bucket_path': bucket_path
        })

    return jsonify(success=True, msg="Received file: {object_id}")
