#!/bin/bash -e

TOPIC=${1:-raw-file-uploaded}

gcloud functions deploy \
  "${TOPIC}" \
  --trigger-topic "${TOPIC}" \
  --entry-point entry_point \
  --memory '256m' \
  --no-allow-unauthenticated \
  --runtime python38 \
  --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
  --update-labels "use=pipeline"
