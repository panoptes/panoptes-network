#!/bin/bash -e

echo "Deploying cloud function: image-received"

gcloud builds submit .
