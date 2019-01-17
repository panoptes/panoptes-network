#!/bin/bash -e

echo "Deploying cloud function"

gcloud functions deploy make-rgb-fits \
	--entry-point make_rgb_fits \
	--runtime python37 \
	--trigger-http
