#!/bin/bash -e

echo "Deploying cloud function: cf-get-observation-state"

gcloud functions deploy \
                 get-observation-state \
                 --entry-point get_state \
                 --runtime python37 \
                 --trigger-http
