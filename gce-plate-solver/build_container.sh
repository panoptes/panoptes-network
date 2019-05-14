#!/bin/bash -e

echo "Building solve-extract Docker GCE instance"

gcloud builds submit \
	--timeout=1500 \
	--tag gcr.io/panoptes-survey/solve-extract
