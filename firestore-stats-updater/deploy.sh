#!/bin/bash -e

gcloud functions deploy \
     firestore-stats-updater-observations-create \
     --entry-point observations_entry \
     --runtime python37 \
     --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
     --update-labels "use=pipeline" \
     --no-allow-unauthenticated \
     --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
     --trigger-resource "projects/panoptes-exp/databases/(default)/documents/observations/{sequence_id}"

gcloud functions deploy \
     firestore-stats-updater-observations-delete \
     --entry-point observations_entry \
     --runtime python37 \
     --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
     --update-labels "use=pipeline" \
     --no-allow-unauthenticated \
     --trigger-event "providers/cloud.firestore/eventTypes/document.delete" \
     --trigger-resource "projects/panoptes-exp/databases/(default)/documents/observations/{sequence_id}"

gcloud functions deploy \
     firestore-stats-updater-images-create \
     --entry-point images_entry \
     --runtime python37 \
     --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
     --update-labels "use=pipeline" \
     --no-allow-unauthenticated \
     --trigger-event "providers/cloud.firestore/eventTypes/document.create" \
     --trigger-resource "projects/panoptes-exp/databases/(default)/documents/images/{image_id}"

gcloud functions deploy \
     firestore-stats-updater-images-delete \
     --entry-point images_entry \
     --runtime python37 \
     --service-account "piaa-pipeline@panoptes-exp.iam.gserviceaccount.com" \
     --update-labels "use=pipeline" \
     --no-allow-unauthenticated \
     --trigger-event "providers/cloud.firestore/eventTypes/document.delete" \
     --trigger-resource "projects/panoptes-exp/databases/(default)/documents/images/{image_id}"

