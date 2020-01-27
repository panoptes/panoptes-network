#!/bin/bash -e

TOPIC=${1:-lookup-field}

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --trigger-http
