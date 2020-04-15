#!/bin/bash -e

TOPIC=${1:-plate-solve}
BASE_TAG=${1:-dev}

gcloud builds submit --substitutions "_TOPIC=${TOPIC},_BASE_TAG=${BASE_TAG}" .
