#!/bin/bash -e

TOPIC=${1:-lookup-catalog-sources}

# Submit a build using Google Cloud Build
gcloud builds submit --tag "gcr.io/panoptes-exp/${TOPIC}"

# Deploy to Cloud Run
gcloud run deploy "${TOPIC}" \
    --port 8080 \
    --platform managed \
    --memory 2Gi \
    --image "gcr.io/panoptes-exp/${TOPIC}"
