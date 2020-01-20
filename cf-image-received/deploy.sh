#!/bin/bash -e

echo "Deploying cloud function: image-received"

TRIGGER_BUCKET="panoptes-raw-images"

gcloud functions deploy \
                 image-received \
                 --entry-point image_received \
                 --runtime python37 \
                 --trigger-resource "${TRIGGER_BUCKET}" \
                 --trigger-event google.storage.object.finalize \
                 --service-account "${SERVICE_ACCOUNT}"

