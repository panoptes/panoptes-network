Raw Image Uploaded Acknowledgement
==================================

This service is triggered when a file is placed in
our [Storage Bucket](https://cloud.google.com/storage/)
(see also the documentation about
using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

The service will receive a PubSub message in a json format. Based on the file type that was uploaded
various actions will be taken:

FITS: Record metadata and move FITS file to `panoptes-raw-images` bucket. Also places a copy
in `panoptes-archive`.

CR2: Forward to the `make-rgb-fits` service. Move to `panoptes-images-raw` bucket.

JPG: No further processing. Move to `panoptes-images-jpgs`.

MP4: Timelapse files are moved to the `panoptes-timelapse` bucket.

Other: All other files are moved to the `panoptes-images-temp` bucket as they shouldn't be placed in
the raw bucket.

Additionally, the function will look for legacy files that have a `field_name` component to their
path. This path will be stripped and the file will be re-uploaded (and processed).

Endpoint: No public endpoint

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.

#### Notification Creation

The bucket notification only needs to be created once, which can be done with the following command:

```sh
gsutil notification create -t raw-file-uploaded -f json -e OBJECT_FINALIZE gs://panoptes-images-incoming/
```

You can list existing notifications with:

```sh
gsutil notification list gs://panoptes-images-incoming/
```
