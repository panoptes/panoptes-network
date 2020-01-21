#!/bin/bash -e

echo "Deploying cloud function: lookup-field"

gcloud functions deploy lookup-field \
	--entry-point lookup_field \
	--runtime python37 \
	--trigger-http
