#!/bin/bash -e

usage() {
  echo -n "##################################################
# Run the make-observation-psc dataflow job.
# 
##################################################
 $ $(basename $0) SEQ_ID [JOB_NAME]
 
 Options:
  SEQ_ID	The Sequence ID of the observation to be processed. Should
  		have underscores as separators, e.g. PAN001_14d3bd_20190304T054407.
  JOB_NAME	The optional job name. If not provided, defaults to the
  		template name and a timestamp.

 Example:
  ./run_dataflow.sh PAN001_14d3bd_20190304T054407
"
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

PROJECT_ID='panoptes-survey'

DATAFLOW_BUCKET='panoptes-dataflow'
SOURCES_BUCKET='panoptes-detected-sources'
PSC_BUCKET='panoptes-observation-psc'

JOB_TEMPLATE='makepsc'

SEQ_ID=${1}
SEQ_PATH=${SEQ_ID//_/\/}
JOB_NAME=${2:-${JOB_TEMPLATE}-${SEQ_ID}-$(date '+%Y%m%dT%H%M%S')}

echo '**********************'
echo 'Starting DataFlow job:'
echo '======================'
echo "SEQ_ID = ${SEQ_ID}"
echo "SEQ_PATH = ${SEQ_PATH}"
echo "JOB_TEMPLATE = ${JOB_TEMPLATE}s"
echo "JOB_NAME = ${JOB_NAME}"
echo '======================'

gcloud dataflow jobs run ${JOB_NAME} \
	--gcs-location gs://${DATAFLOW_BUCKET}/${JOB_TEMPLATE}/${JOB_TEMPLATE} \
	--parameters input="gs://${SOURCES_BUCKET}/${SEQ_PATH}/*.csv" \
	--parameters pscs_output="gs://${PSC_BUCKET}/${SEQ_PATH}.csv" \
	--parameters scores_output="gs://${PSC_BUCKET}/${SEQ_PATH}-scores.csv"
