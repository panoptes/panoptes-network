#!/bin/bash -e

TOPIC=${1:-observation-file-uploaded}
LOG_LEVEL=${2:-DEBUG}

gcloud functions deploy \
  "${TOPIC}" \
  --entry-point entry_point \
  --memory '2Gi' \
  --timeout '300s' \
  --runtime python38 \
  --no-allow-unauthenticated \
  --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
  --update-labels "use=pipeline" \
  --set-env-vars "LOG_LEVEL=${LOG_LEVEL}" \
  --trigger-topic "${TOPIC}"
