# PANOPTES Data Explorer

- [PANOPTES Data Explorer](#panoptes-data-explorer)
  - [Data Model](#data-model)
  - [Data Input](#data-input)
  - [Data Output](#data-output)
  - [Data Descriptions](#data-descriptions)
    - [Unit](#unit)
    - [Observation](#observation)
    - [Image](#image)
    - [Star](#star)
    - [Lightcurve](#lightcurve)

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

```md
# Data Model
Units
  Mount
  Sensors
  Cameras
    Observations
        Images

```

```md
# Data Output
Processed Observations
Lightcurves
```

> **Note:** We currently are not generating any data products for the `mount` or `sensors`.

## Data Input
<a href="#" id="data-input"></a>

| object      |  key           | example                         | description   
|-------------|--------------- | --------------------------------|------------ 
| Unit        | `unit_id`      | `PAN001`                        | Data for a given PANOPTES units.
| Camera        | `camera_id`      | `14d3bd`                        | Camera id.
| Observation | `sequence_id`  | `PAN012_95cdbc_20191025T023224` | A sequence of images defined by a mount slew.
| Image       | `image_id`     | `PAN012_95cdbc_20191025T023434` | A single image at a set exposure.

## Data Output
<a href="#" id="data-output"></a>

| object      |  key          | example                         | description   
|-------------|---------------|---------------------------------|--------------
| Star        | `picid`       | `1954452882`                    | Data about the stellar source.
| Lightcurve  | `lcid`        | `1954452882_20200110T122127`    | Generated lightcurve data from a single processing run.

## Data Descriptions
<a href="#" id="data-descriptions"></a>

> :warning: Note: PANOPTES data is stored in [Firestore](https://firebase.google.com/docs/firestore), which is a NoSQL database.
Unlike a traditional database, this means that there is no guarantee that a certain field will be present. As part of our processing we try to guarantee that the fields listed below are always present, however the document may also contain additional fields not documented here.

### Unit

The unit information is organized by `unit_id`, (e.g., `PAN010`).



```json
{
    PAN001: {
        name: "PAN001",
        elevation: 3400.0,      # meters
        location: {             # stored as GeoPoint
            latitude: 19.54,    # degrees
            longitude: -155.58  # degrees
        },
        status: "active"
    }
}
```

### Observation

An observation is a sequence of images from a single camera taken from a single unit during one continuous
tracking movement. Any movement of the mount (e.g. a meridian flip) will stop the current observation, even if
the same target is observed next. Ideally a unit will have at least two simulataneous observations at any
given time (one for each camera).

Observations are organized by a `sequence_id` of the form: 

`<UNIT_ID>_<CAMERA_ID>_<SEQUENCE_START_TIME>`.

```json
{
    PAN001_14d3bd_20180216T110623: {
        unit_id: "PAN001",
        status: "receiving_files",
        camera_id: "14d3bd",
        software_version: "POCSv0.6.0",
        ra: 135.859993568,
        dec: 28.4376569571,
        exptime: 120
        time: DatetimeWithNanoseconds(2018, 2, 16, 11, 6, 23, tzinfo=<UTC>),
    }
}
```

### Image

An image corresponds to a single image from a single camera.

Images are organized by an `image_id` of the form: 

`<UNIT_ID>_<CAMERA_ID>_<IMAGE_START_TIME>`.

```json
{
PAN001_14d3bd_20180216T112430: {
    ha_mnt: 1.919988307895942,       # From the mount
    ra_mnt: 133.1505416666667,       # From the mount
    dec_mnt: 28.33138888888889,      # From the mount
    ra_image: 135.884026231,         # From plate solve
    dec_image: 28.3746828541,        # From plate solve
    exptime: 120,
    moonfrac: 0.003716693699630014,
    moonsep: 21.88964559220797,
    airmass: 1.126544582361047,
    bucket_path: "PAN001/14d3bd/20180216T110623/20180216T112430.fits.fz",
    sequence_id: "PAN001_14d3bd_20180216T110623",
    time: DatetimeWithNanoseconds(2018, 2, 16, 11, 24, 30, tzinfo=<UTC>),
    status: "uploaded"
  }    
}
```

### Star

Stellar information is identified by the PANOPTES Input Catalog ID (PICID) and consists of processed runs
of a single observation. An observation could be processed in multiple ways by the processing run.

Note that the PICID corresponds the the Tess Input Catalog ID (TICID) and thus the same number can be used
as a lookup on many public sites.

### Lightcurve

_coming soon..._