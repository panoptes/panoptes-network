#!/bin/bash -e

TOPIC=${1:-image-uploaded}
BUCKET_NAME="panoptes-raw-images"

gcloud functions deploy \
                 "${TOPIC}" \
                 --entry-point entry_point \
                 --runtime python37 \
                 --no-allow-unauthenticated \
                 --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
                 --update-labels "use=pipeline" \
                 --trigger-resource "${BUCKET_NAME}" \
                 --trigger-event google.storage.object.finalize
