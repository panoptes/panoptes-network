#!/bin/bash -e

SERVICE_NAME=${1:-image-uploaded}

echo "Deploying service: ${SERVICE_NAME}"

gcloud builds submit --substitutions SERVICE_NAME="${SERVICE_NAME}" .
