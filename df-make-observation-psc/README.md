# Make Observation PSC

Create a dataflow [job template](https://cloud.google.com/dataflow/docs/guides/templates/overview) that, given a sequence_id, will gather CSV files from the panoptes-detected-sources bucket and consolidate them into one large master PSC collection.

This file is then uploaded to the `panoptes-observation-psc` bucket, which will trigger a pubsub message (see the similar source finder [readme](https://github.com/panoptes/panoptes-network/tree/master/gce-find-similar-sources) for details). 

The `deploy.sh` script will make a new version of the template stored in a storage
bucket and should be run any time the `makepsc.py` file changes.

> :bulb: Note: The `deploy.sh` script requires a python2.7 environment and the `apache-beam[gcp]` module.

The `run_dataflow.sh` script will run the job template with the DataFlow runner
(i.e. in the cloud) and requires a `sequence_id` parameter to run.

`run_locally.sh` will attempt to run the job locally.
