#!/bin/bash -e

gcloud functions deploy \
                 observation-psc-created \
                 --entry-point observation_psc_created \
                 --runtime python37 \
                 --trigger-resource panoptes-observation-psc \
                 --trigger-event google.storage.object.finalize
