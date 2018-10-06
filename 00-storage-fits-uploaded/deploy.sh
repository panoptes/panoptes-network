#!/bin/bash -e

gcloud functions deploy \
                 00-storage-fits-uploaded \
                 --entry-point ack_fits_received \
                 --runtime python37 \
                 --trigger-resource panoptes-survey \
                 --trigger-event google.storage.object.finalize
