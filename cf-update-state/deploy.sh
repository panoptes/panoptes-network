#!/bin/bash -e

echo "Deploying cloud function: cf-update-state"

gcloud functions deploy \
                 update-state \
                 --entry-point update_state \
                 --runtime python37 \
                 --trigger-http