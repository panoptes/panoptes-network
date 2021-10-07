#!/bin/bash -e

TOPIC=${1:-raw-file-uploaded}

gcloud functions deploy \
  "${TOPIC}" \
  --trigger-topic "${TOPIC}" \
  --entry-point entry_point \
  --memory '2048m' \
  --no-allow-unauthenticated \
  --runtime python39 \
  --ingress-settings=internal-and-gclb \
  --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
  --update-labels "use=pipeline"
