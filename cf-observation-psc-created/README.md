File Upload to Bucket Storage
=============================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

Triggered when a new PSC file is uploaded for an observation.

The Observation PSC is created by the `df-make-observation-pc` job, which will
upload a CSV file to the `panoptes-observation-psc` bucket. This CF will listen
to that bucket and process new files:

    1. Update the `metadata.sequences` table with the RA/Dec boundaries for
    the sequence.
    2. Send a PubSub message to the `find-similar-sources` topic to trigger
    creation of the similar sources.

Endpoint: No public endpoint


Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

> :bulb: There is also a small convenience script called `deploy.sh` that does the same thing. 
```bash
./deploy.sh
```

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `observation-psc-created`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 observation-psc-created \
                 --entry-point observation_psc_created \
                 --runtime python37 \
                 --trigger-resource panoptes-observation-psc \
                 --trigger-event google.storage.object.finalize
```
