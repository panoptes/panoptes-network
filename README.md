# PANOPTES Data Explorer

The PANOPTES Data Explorer can be used to find information about PANOPTES data organized by:

* Unit
* Observation
* Star

* `unit_id`: `PAN001`
* `sequence_id`: `PAN001_14d3bd_20200109T052127`
* `picid`: `1954452882`

### Unit Information

The unit information is organized by `unit_id`, (e.g., `PAN010`).

### Observation Information

An observation is a sequence of images from a single camera taken from a single unit during one continuous
tracking movement. Any movement of the mount (e.g. a meridian flip) will stop the current observation, even if
the same target is observed next. Ideally a unit will have at least two simulataneous observations at any
given time (one for each camera).

Observations are organized by a `sequence_id` of the form: `<UNIT_ID>_<CAMERA_ID>_<SEQUENCE_START_TIME>`.

### Stellar Information

Stellar information is identified by the PANOPTES Input Catalog ID (PICID) and consists of processed runs
of a single observation. An observation could be processed in multiple ways by the processing run.

Note that the PICID corresponds the the Tess Input Catalog ID (TICID) and thus the same number can be used
as a lookup on many public sites.

## Data Ingress

See the [panoptes-network](https://github.com/panoptes/panoptes-network) repo for details on how the data is
processed.
