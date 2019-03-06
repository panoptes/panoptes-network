File Upload to Bucket Storage
=============================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function acknowledges a [PubSub](https://cloud.google.com/pubsub/) message
that is sent when a file is placed in our [Storage Bucket](https://cloud.google.com/storage/) 
(see also the documentation about using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

Triggered when file is uploaded to bucket. 

FITS: Set header variables and then forward to endpoint for adding headers
	to the metadatabase.
CR2: Trigger the creation of the RGB fits images, pretty JPG/PNG images for viewing,
	and timelapse videos.

Endpoint: No public endpoint


Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `bucket-upload`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 bucket-upload \
                 --entry-point bucket_upload \
                 --runtime python37 \
                 --trigger-resource panoptes-survey \
                 --trigger-event google.storage.object.finalize
```

> :bulb: There is also a small convenience script called `deploy.sh` that does the same thing. 
```bash
./deploy.sh
```