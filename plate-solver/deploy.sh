#!/bin/bash -e

TOPIC=${1:-plate-solve}

gcloud builds submit --substitutions "_TOPIC=${TOPIC}" .
