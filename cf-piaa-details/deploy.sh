#!/bin/bash -e

echo "Deploying cloud function: get-piaa-details"

gcloud functions deploy get-piaa-details \
	--entry-point get_piaa_details \
	--runtime python37 \
	--memory 512MB \
	--trigger-http
