#!/bin/bash -e

python testbeam.py --runner DataflowRunner --project panoptes-survey --stage_location gs://panoptes-test-bucket/dataflow/staging --temp_location gs://panoptes-test-bucket/dataflow/temp --template_location gs://panoptes-test-bucket/testbeam
