#!/bin/bash -e

TOPIC=${1:-calibrate-images}

gcloud functions deploy \
  "${TOPIC}" \
  --trigger-topic "${TOPIC}" \
  --entry-point entry_point \
  --memory "4G" \
  --no-allow-unauthenticated \
  --runtime python38 \
  --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
  --timeout 540 \
  --update-labels "use=pipeline"
