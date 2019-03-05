#!/bin/bash -e

echo "Deploying cloud function: extract-sources"

gcloud functions deploy \
                 extract-sources \
                 --entry-point extract_sources \
                 --runtime python37 \
                 --trigger-http
