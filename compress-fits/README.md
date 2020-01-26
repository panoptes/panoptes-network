Compress FITS
-------------

A [Google Cloud Run](https://cloud.google.com/run/) service that will compress `.fits` files to `.fits.fz`.

This services is based on the `panoptes-utils` base docker image and uses the
`panoptes.utils.images.fits.fpack` utility function.

The service is triggered automatically by the `image-uploaded` service when a `fits` file is received.

Note that all Cloud Run services are web servers responding on http ports. When using
PubSub, GCP automatically performs some validation and delivers the PubSub message
as a json document in a regular POST request. See the documentation for
[Cloud Run PubSub Triggers](https://cloud.google.com/run/docs/triggering/pubsub-push)

### Deploy

From the `panoptes-network` root directory:

```bash
bin/deploy compress-fits
```
