#!/bin/bash -e

TOPIC=${1:-image-uploaded}
BUCKET_NAME="panoptes-raw-images"

echo "Deploying service for topic: ${TOPIC}"

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --trigger-resource "${BUCKET_NAME}" \
                 --trigger-event google.storage.object.finalize
