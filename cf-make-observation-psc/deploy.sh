#!/bin/bash -e

echo "Deploying cloud function: make-observation-psc"

gcloud functions deploy make-observation-psc \
	--entry-point make_observation_psc \
	--runtime python37 \
	--timeout 120s \
	--memory 1024MB \
	--trigger-http
