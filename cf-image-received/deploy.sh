#!/bin/bash -e

gcloud functions deploy \
                 ack-image-received \
                 --entry-point ack_image_received \
                 --runtime python37 \
                 --trigger-resource panoptes-survey \
                 --trigger-event google.storage.object.finalize
