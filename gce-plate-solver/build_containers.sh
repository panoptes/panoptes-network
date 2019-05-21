#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-network/gce-plate-solver

echo "Building solve-extract Docker GCE instance"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/cloudbuild.yaml" \
    ${SOURCE_DIR}

# echo "Updating GCE container"
# IMAGE_NAME="gcr.io/panoptes-survey/solve-extract@sha-256:XXXXXX"
# gcloud compute instances update-container solve-and-extract --container-image "${IMAGE_NAME}"
