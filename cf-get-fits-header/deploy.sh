#!/bin/bash -e

echo "Deploying cloud function: cf-get-fits-header"

gcloud functions deploy \
                 get-fits-header \
                 --entry-point get_fits_header \
                 --runtime python37 \
                 --trigger-http
