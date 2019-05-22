#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-network/gce-find-similar-sources

echo "Building find-similar-sources Docker GCE instance"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/cloudbuild.yaml" \
    ${SOURCE_DIR}

# echo "Updating GCE container"
# IMAGE_NAME="gcr.io/panoptes-survey/find-similar-sources@sha-256:XXXXXX"
# gcloud compute instances update-container find-similar-sources --container-image "${IMAGE_NAME}"
