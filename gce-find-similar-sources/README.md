# Similar Source Finder

A script that listens to the PubSub subscription `gce-find-similar-sources` which
contains either an `object_id` or `sequence_id` attribute. The `object_id` is the 
path name from the `panoptes-observation-psc` bucket and the PubSub message is
triggered upon upload of a new master PSC collection file for an observation (which
is a result of an `df-make-observation-psc` job). The `sequence_id` could come
from a PubSub message that is manually triggered (e.g. for testing) or via a cloud
function. The `object_id` contains the `sequence_id` in it.

Downloads the PSC collection file, filters the sources to just those that appear in
the majority of all frames, then loops each source to find the most "similar" sources
according to the sum of the sum of squared differences. Writes CSV file for each
source (PICID).