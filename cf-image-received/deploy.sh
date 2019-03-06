#!/bin/bash -e

echo "Deploying cloud function: image-received"

gcloud functions deploy \
                 image-received \
                 --entry-point image_received \
                 --runtime python37 \
                 --trigger-http
