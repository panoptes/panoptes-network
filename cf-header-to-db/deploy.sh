#!/bin/bash -e

echo "Deploying cloud function: cf-header-to-db"

gcloud functions deploy \
                 header-to-db \
                 --entry-point header_to_db \
                 --runtime python37 \
                 --trigger-http