#!/bin/bash -e

TOPIC=${1:-fits-packer}

gcloud builds submit --substitutions "_TOPIC=${TOPIC}" .
