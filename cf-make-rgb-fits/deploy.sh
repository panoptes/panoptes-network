#!/bin/bash -e

echo "Deploying cloud function: make-rgb-fits"

gcloud functions deploy make-rgb-fits \
	--entry-point make_rgb_fits \
	--runtime python37 \
	--memory 512MB \
	--trigger-http \
    --service-account "${SERVICE_ACCOUNT}"
