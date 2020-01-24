#!/bin/bash -e

echo "Deploying cloud function: image-uploaded"

gcloud builds submit .
