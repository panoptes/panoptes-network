#!/bin/bash -e

TOPIC=${1:-lookup-catalog-sources}
BASE_TAG=${1:-latest}

gcloud builds submit --substitutions "_TOPIC=${TOPIC},_BASE_TAG=${BASE_TAG}" .
