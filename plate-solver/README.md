Plate Solver
------------

An astronomical plate-solving service!

This service is based on the `panoptes-utils` base docker image and uses the
`panoptes.utils.images.fits.get_solve_field` utility function.

The service is triggered automatically by the `raw-file-uploaded` [PubSub](https://cloud.google.com/run/docs/triggering/pubsub-push) topic when a `fits` (or `.fz`) file is uploaded to the `panoptes-incoming` bucket.

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
