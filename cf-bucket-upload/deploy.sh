#!/bin/bash -e

gcloud functions deploy \
                 bucket-upload \
                 --entry-point bucket_upload \
                 --runtime python37 \
                 --trigger-resource panoptes-survey \
                 --trigger-event google.storage.object.finalize
