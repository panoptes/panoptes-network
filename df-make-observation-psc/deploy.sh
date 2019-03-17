#!/bin/bash -e

PROJECT_ID='panoptes-survey'
BUCKET_NAME='panoptes-dataflow'
JOB_NAME='makepsc'

echo "Sending DataFlow template to template bucket."

python ${JOB_NAME}.py --runner DataflowRunner \
	--project ${PROJECT_ID} \
	--stage_location gs://${BUCKET_NAME}/${JOB_NAME}/staging \
	--temp_location gs://${BUCKET_NAME}/${JOB_NAME}/temp \
	--template_location gs://${BUCKET_NAME}/${JOB_NAME}/${JOB_NAME}
