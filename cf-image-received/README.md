Acknowledge FITS File Received
==============================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is triggered  when a file is placed in our [Storage Bucket](https://cloud.google.com/storage/)
(see also the documentation about using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

FITS: Set header variables and then forward to endpoint for adding headers
	to the metadatabase.
CR2: Trigger the creation of the RGB fits images, pretty JPG/PNG images for viewing,
	and timelapse videos.

> :memo: Todo: Trigger timelapse and pretty image creation from here.

Endpoint: No public endpoint


Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `image-received`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 image-received \
                 --entry-point image_received \
                 --runtime python37 \
                 --trigger-resource "${TRIGGER_BUCKET}" \
                 --trigger-event google.storage.object.finalize
```

> :bulb: There is also a small convenience script called `deploy.sh` that does the same thing.

```bash
./deploy.sh
```
