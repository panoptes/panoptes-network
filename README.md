# PANOPTES Data Explorer

The PANOPTES Data Explorer can be used to find information about PANOPTES data.

This page gives an overview of how the data is logically organized (the [data model](#data-odel)),
how it is captured by each PANOPTES unit ([data input](#data-input)), and how the
data is then made publically available ([data output](#data-output)).

The [PIAA pipeline](https://github.com/panoptes/PIAA) is responsible for moving the 
data from the units (input) to the public (output) while always respecting the data model.

The data is described in more detail [below](#data-desc).

## Data Model
<a href="#" id="data-model"></a>

Data is organized by the object type:

```
# Data Input
* Units
  * Mount
  * Sensors
  * Cameras
    * Observations
        * Images


# Data Output
* Sources
  * Observations
    * Lightcurves

```

> **Note:** We currently are not generating any data products for the `mount` or `sensors`.

## Data Input
<a href="#" id="data-input"></a>

| object      |  key           | example                         | description   
|-------------|--------------- | --------------------------------|------------ 
| Unit        | `unit_id`      | `PAN001`                        | Data for a given PANOPTES units.
| Observation | `sequence_id`  | `PAN001_14d3bd_20200109T052127` | A sequence of images defined by a mount slew.
| Image       | `image_id`     | `PAN001_14d3bd_20200109T052127` | A single image at a set exposure.

## Data Output
<a href="#" id="data-output"></a>

| object      |  key          | example                         | description   
|-------------|---------------|---------------------------------|--------------
| Star        | `picid`       | `1954452882`                    | Data about the stellar source.
| Lightcurve  | `lcid`        | `1954452882_20200110T122127`    | Generated lightcurve data from a single processing run.

## Data Descriptions
<a href="#" id="data-desc"></a>

### Unit

The unit information is organized by `unit_id`, (e.g., `PAN010`).

### Observation

An observation is a sequence of images from a single camera taken from a single unit during one continuous
tracking movement. Any movement of the mount (e.g. a meridian flip) will stop the current observation, even if
the same target is observed next. Ideally a unit will have at least two simulataneous observations at any
given time (one for each camera).

Observations are organized by a `sequence_id` of the form: `<UNIT_ID>_<CAMERA_ID>_<SEQUENCE_START_TIME>`.

### Image

### Star

Stellar information is identified by the PANOPTES Input Catalog ID (PICID) and consists of processed runs
of a single observation. An observation could be processed in multiple ways by the processing run.

Note that the PICID corresponds the the Tess Input Catalog ID (TICID) and thus the same number can be used
as a lookup on many public sites.

### Lightcurve