#!/bin/bash -e

TOPIC=${1:-calibrate-images}

gcloud functions deploy \
  "${TOPIC}" \
  --entry-point entry_point \
  --runtime python38 \
  --no-allow-unauthenticated \
  --memory "4G" \
  --timeout 540 \
  --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
  --update-labels "use=pipeline" \
  --trigger-topic "${TOPIC}"
