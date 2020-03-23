#!/bin/bash -e

TOPIC=${1:-make-rgb-fits}

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
                 --update-labels "use=pipeline" \
                 --trigger-topic "${TOPIC}"
