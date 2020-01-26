Compress FITS
-------------

A [Google Cloud Run](https://cloud.google.com/run/) service that will compress `.fits` files to `.fits.fz`.

This services is based on the `panoptes-utils` base docker image and uses the
`panoptes.utils.images.fits.fpack` utility function.

The service is triggered automatically by the `image-uploaded` service when a `fits` file is received.

### Deploy

From the `panoptes-network` root directory:

```bash
bin/deploy compress-fits
```
