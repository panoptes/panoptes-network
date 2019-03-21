#!/bin/bash -e

echo "Docker GCE instance to find similar sources for each PSC in an observation."

gcloud builds submit \
	--timeout=1500 \
	--tag gcr.io/panoptes-survey/find-similar-sources
