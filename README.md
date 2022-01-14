PANOPTES Network
================

- [PANOPTES Network](#panoptes-network)
    - [Data Model](#data-model)
        - [Overview](#data-overview)
        - [Keys](#data-keys)
        - [Data Descriptions](#data-descriptions)
            - [Unit](#unit)
            - [Observation](#observation)
            - [Image](#image)
            - [Star](#star)
            - [Lightcurve](#lightcurve)
    - [Data Explorer](#data-explorer)
    - [Functions](#functions)
    - [Development](#development)
        - [Setup](#setup)

Software related to the wider PANOPTES network that ties the individual units together. This is a repository to host the
various Google Cloud Platform services.

The repository uses a number of Google Cloud Platform productions, including the Data Explorer (`data-explorer/`) and a
number of [Cloud Functions](https://cloud.google.com/functions).

The Cloud Functions largely communicate with each other via [PubSub](https://cloud.google.com/pubsub/)
messages based on certain events, such as when an image is uploaded or when a certain processing step is complete.

## Data Model

### Overview

<a href="#" id="data-overview"></a>

The data model for the PANOPTES units and the Observations and Images they take is a simple nested structure based on
the unit id (e.g. `PAN023`), see [Data Descriptions](#data-descriptions) below. Data is stored
in [Google Firestore](https://firebase.google.com/docs/firestore).

The basic model is that a `unit` has `observations` that contain `images`. Each level has a corresponding document for
metadata, so an individual `unit` also has a `name`, `latitude`, `longitude`, etc. In Firestore these are called "
collections" and "documents": we have a `units` collection that contains zero or more
`unit` documents; a `unit` document has an associated `observations` collection, etc.

### Keys

<a href="#" id="data-keys"></a>

Each document in a collection can be identified by a unique key:

| collection               | key           | key example                     | description                                                                               |
| ------------------------ | ------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |
| `images`                 | `image_id`    | `PAN012_95cdbc_20191025T023434` | A single image at a set exposure.                                                         |
| `observations`           | `sequence_id` | `PAN012_95cdbc_20191025T023224` | A sequence of images defined by a mount slew.                                             |
| `units`                  | `unit_id`     | `PAN001`                        | Data for a given PANOPTES unit.                                                           |

### Data Descriptions

<a href="#" id="data-descriptions"></a>

> :warning: Note: PANOPTES data is stored in [Firestore](https://firebase.google.com/docs/firestore), which is a NoSQL database. Unlike a traditional database, this means that there is no guarantee that a certain field will be present. As part of our processing we try to guarantee that the fields listed below are always present, however the document may also contain additional fields not documented here.

#### Unit

Collection: `units`
Document ID: `unit_id`

```py
{
    "PAN001": {
        "name": "PAN001",
        "elevation": 3400.0,  # meters
        "location": {  # stored as GeoPoint
            "latitude": 19.54,  # degrees
            "longitude": -155.58  # degrees
        },
        "num_images": 139299,
        "num_observations": 3618,
        "total_minutes_exptime": 259657.21
        "status": "active"
    }
}
```

#### Observation

An observation is a sequence of images taken from a single camera from a single unit during one continuous tracking
movement. Any movement of the mount (e.g. a meridian flip) will stop the current observation, even if the same target is
observed next. Ideally a unit will have at least two simulataneous observations at any given time (one for each camera).

Observations are organized by a `sequence_id` of the form:

`<UNIT_ID>_<CAMERA_ID>_<SEQUENCE_START_TIME>`.

Collection: `observations`
Document ID: `sequence_id`
Notes:

* An observation will always have `ra` and `dec` columns but the values may be `null`. Typically this indicates the file
  has not been properly plate-solved.

```py
{
    "PAN001_14d3bd_20180216T110623": {
        "unit_id": "PAN001",
        "camera_id": "14d3bd",
        "software_version": "POCSv0.6.0",
        "ra": 135.859993568,
        "dec": 28.4376569571,
        "exptime": 120,
        "status": "receiving_files",
        "time": DatetimeWithNanoseconds(2018, 2, 16, 11, 6, 23, tzinfo= < UTC >),
"received_time": DatetimeWithNanoseconds(2020, 5, 1, 11, 6, 23, tzinfo= < UTC >),
"num_images": 10,
"total_minutes_exptime": 20
}
}
```

#### Image

An image corresponds to a single image from a single camera.

Images are organized by an `image_id` of the form:

`<UNIT_ID>_<CAMERA_ID>_<IMAGE_START_TIME>`.

Collection: `images`
Document ID: `image_id`

```py
{
    "PAN001_14d3bd_20180216T112430": {
        "ha_mnt": 1.919988307895942,  # From the mount
        "ra_mnt": 133.1505416666667,  # From the mount
        "dec_mnt": 28.33138888888889,  # From the mount
        "ra_image": 135.884026231,  # From plate solve
        "dec_image": 28.3746828541,  # From plate solve
        "exptime": 120,
        "moonfrac": 0.003716693699630014,
        "moonsep": 21.88964559220797,
        "airmass": 1.126544582361047,
        "bucket_path": "PAN001/14d3bd/20180216T110623/20180216T112430.fits.fz",
        "public_url": "https://storage.googleapis.com/panoptes-raw-images/PAN001/14d3bd/20180216T110623/20180216T112430.fits.fz",
        "sequence_id": "PAN001_14d3bd_20180216T110623",
        "status": "solved",
        "solved": True,
        "time": DatetimeWithNanoseconds(2018, 2, 16, 11, 24, 30, tzinfo= < UTC >)
}
}
```

#### Star

_coming soon..._

#### Lightcurve

_coming soon..._

## Data Explorer
<a href="#" id="data-explorer"></a>

The Data Explorer is a web-based tool to explore PANOPTES data at the observation and lightcurve level.

See [Data Explorer README](data-explorer/README.md) for details.

## Functions

<a href="#" id="functions"></a>

There are a few different categories of functions that are in use on the panoptes-network.

| Service                                        | Trigger | Description                                                     |
| ---------------------------------------------- | ------- | --------------------------------------------------------------- |
| [`raw-file-uploaded`](image-uploaded/README.md)   | Bucket  | Simple foward to next service based on file type.               |
| [`make-rgb-fits`](make-rgb-fits/README.md)     | PubSub  | Makes interpolated RGB `.fits` from `.CR2` file.                |
| [`lookup-field`](lookup-field/README.md)       | Http    | A simple service to lookup astronomical sources by search term. |
| [`get-fits-header`](get-fits-header/README.md) | Http    | Returns the FITS headers for a given file.                      |

## Development

> See also the [Development](https://github.com/panoptes/panoptes-utils/#development) section of `panoptes-utils` for an easier docker version.

Development within the `panoptes-network` repository could be related to either the updating of individual GCP services
or could be related to [Data Explorer](#data-explorer).

For the individual services the work is usually constrained to a single service/folder within this repository and the
changes can be published according to the [Deploying services](#deploying-services) section above.

### Setup

You must first have an environment that has the approriate software installed.

The easiest way to do this with an [Anaconda](https://www.anaconda.com/) environment. Assuming you already have `conda`
installed (see link for details):

```bash
cd $PANDIR/panoptes-network

# Create environment for panoptes-network
conda create -n panoptes-network python=3.7 nodejs=10

# Activate environment
conda activate panoptes-network

# Install python dependencies
pip install -r requirements.txt

# Install javascript dependencies
npm run install-deps
```

The javascript dependencies will also install the [`firebase-tools`](https://firebase.google.com/docs/cli/) that are
required to work with the local emulators. These tools require that you login to firebase:

```bash
firebase login
```

This should open a browser and ask you to authenticate with your gmail account.

For instructions on working with the Data Explorer, see the [Development section](data-explorer#data-explorer/README.md)
of the README.

> Note: You need to to have the Java OpenJDK to run the emulators. Details at [https://openjdk.java.net/install](https://openjdk.java.net/install).
