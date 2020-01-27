#!/bin/bash -e

TOPIC=${1:-compress-fits}

gcloud builds submit --substitutions "_TOPIC=${TOPIC}" .
