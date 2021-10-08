#!/bin/bash -e

TOPIC=${1:-data-explorer}
BASE_TAG=${1:-develop}

gcloud builds submit --substitutions "_TOPIC=${TOPIC},_BASE_TAG=${BASE_TAG}" .
