#!/bin/bash -e

TRIGGER_BUCKET="panoptes-raw-images"

gcloud functions deploy \
                 bucket-upload \
                 --entry-point bucket_upload \
                 --runtime python37 \
                 --trigger-resource "${TRIGGER_BUCKET}" \
                 --trigger-event google.storage.object.finalize
