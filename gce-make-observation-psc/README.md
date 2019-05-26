# Make Observation PSC

A script that listens to the PubSub subscription `make-observation-psc` which
contains a `sequence_id` attribute. The `sequence_id` could come from a PubSub
message that is manually triggered (e.g. for testing) or via a cloud function.

Downloads the detected sources CSV files for each frame, filters the sources to
just those that appear in the majority of all frames, then loops each source to
find the most "similar"sources according to the sum of the sum of squared
differences. Writes CSV file for each source (PICID) to the `panoptes-observations-psc`
bucket.

Contained in the folder is a Dockerfile and a `deploy.sh` script for creating a
container image in the Google Container Registry.
