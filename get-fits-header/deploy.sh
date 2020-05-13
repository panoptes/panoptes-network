#!/bin/bash -e

TOPIC=${1:-get-fits-header}

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --allow-unauthenticated \
                 --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
                 --update-labels "use=pipeline" \
                 --trigger-http
