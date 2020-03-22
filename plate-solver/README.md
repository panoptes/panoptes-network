Plate Solver
------------

A [Google Cloud Run](https://cloud.google.com/run/) astronomical plate-solving service!

This services is based on the `panoptes-utils` base docker image and uses the
`panoptes.utils.images.fits.get_solve_field` utility function.

The service is triggered automatically by the `record-image` service when a `fits` file is received.

Note that all Cloud Run services are web servers responding on http ports. When using
PubSub, GCP automatically performs some validation and delivers the PubSub message
as a json document in a regular POST request. See the documentation for
[Cloud Run PubSub Triggers](https://cloud.google.com/run/docs/triggering/pubsub-push)

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
