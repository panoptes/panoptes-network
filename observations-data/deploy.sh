#!/bin/bash -e

echo "Deploying cloud function"

gcloud functions deploy get-observations-data \
	--entry-point get_observations_data \
	--runtime python37 \
	--trigger-http