#!/bin/bash -e

echo "Deploying cloud function: cf-update-observation-state"

gcloud functions deploy \
                 update-observation-state \
                 --entry-point update_state \
                 --runtime python37 \
                 --trigger-http
