#!/bin/bash -e

TOPIC=${1:-image-uploaded}

echo "Deploying service for topic: ${TOPIC}"

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --trigger-topic "${TOPIC}"
