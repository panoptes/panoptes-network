#!/bin/bash -e

TOPIC=${1:-lookup-catalog-sources}

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --update-labels "use=pipeline" \
                 --timeout 300 \
                 --trigger-topic "${TOPIC}"
