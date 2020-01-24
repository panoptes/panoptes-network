Image Uploaded Acknowledgement
==============================

This service is triggered  when a file is placed in our [Storage Bucket](https://cloud.google.com/storage/)
(see also the documentation about using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

The service will receive a PubSub message in a json format. Based on the file
type that was uploaded various actions will be taken:

FITS.FZ: Forward to the `record-image` service.
FITS: Forward to the `fits-packer` service.
CR2: Forward to the `make-rgb-fits` service.

Endpoint: No public endpoint


Deploy
------

The service is run on [Google Cloud Run](https://cloud.google.com/run/docs/). The
deployment script will build a docker image and then set up a new revision of
the cloud run service. See `cloudbuild.yaml` for details.


```bash
./deploy.sh
```
