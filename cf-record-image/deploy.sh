#!/bin/bash -e

echo "Deploying cloud function: cf-record-image"

gcloud functions deploy \
                 record-image \
                 --entry-point record_image \
                 --runtime python37 \
                 --trigger-http \
                 --service-account "${SERVICE_ACCOUNT}"
