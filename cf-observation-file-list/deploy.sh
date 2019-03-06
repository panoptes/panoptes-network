#!/bin/bash -e

echo "Deploying cloud function"

gcloud functions deploy observation-file-list \
	--entry-point get_file_list \
	--runtime python37 \
	--trigger-http