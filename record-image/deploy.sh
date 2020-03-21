#!/bin/bash -e

TOPIC=${1:-record-image}

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --trigger-topic "${TOPIC}"
