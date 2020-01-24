#!/bin/bash -e

echo "Deploying service: image-uploaded"

gcloud builds submit .
