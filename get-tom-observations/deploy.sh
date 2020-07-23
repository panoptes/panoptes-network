#!/bin/bash -e

TOPIC=${1:-get-tom-observations}

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --service-account "panoptes-exp@appspot.gserviceaccount.com" \
                 --update-labels "use=scheduler" \
                 --trigger-http
