Acknowledge FITS File Received
==============================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function acknowledges a [PubSub](https://cloud.google.com/pubsub/) message
that is sent when a file is placed in our [Storage Bucket](https://cloud.google.com/storage/) 
(see also the documentation about using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

The function will check for FITS files and pass the header information to
the `add-header-to-db` cloud function.

> :memo: Todo: Trigger plate-solving here.

> :memo: Todo: Trigger timelapse and pretty image creation from here.

> :memo: Todo: Document that explains overall structure.

Endpoint: No public endpoint


Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `header-to-metadb`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 header-to-metadb \
                 --entry-point header_to_db \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing. 
```bash
./deploy.sh
```