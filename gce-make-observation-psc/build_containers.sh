#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-network/gce-make-observation-psc

echo "Building make-observation-psc Docker GCE instance"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/cloudbuild.yaml" \
    ${SOURCE_DIR}

# echo "Updating GCE container"
# IMAGE_NAME="gcr.io/panoptes-survey/make-observation-psc@sha-256:XXXXXX"
# gcloud compute instances update-container make-observation-psc-1 --container-image "${IMAGE_NAME}"
