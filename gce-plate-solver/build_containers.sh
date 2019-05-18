#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-network/gce-plate-solver

echo "Building solve-extract Docker GCE instance"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/cloudbuild.yaml"

echo "Updating GCE container"
gcloud compute instances update-container solve-and-extract
