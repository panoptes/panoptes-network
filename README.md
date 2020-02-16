PANOPTES Network
================

- [PANOPTES Network](#panoptes-network)
  - [Data Model](#data-model)
    - [Data Descriptions](#data-descriptions)
      - [Unit](#unit)
      - [Observation](#observation)
      - [Image](#image)
      - [Star](#star)
      - [Lightcurve](#lightcurve)
  - [Data Explorer](#data-explorer)
  - [Services](#services)
    - [Deploying services](#deploying-services)
    - [Creating new services](#creating-new-services)
  - [Development](#development)
    - [Setup](#setup)


Software related to the wider PANOPTES network that ties the individual units together.
This is a repository to host the various Google Cloud Platform services.

Each subfolder defines a different service.

Each service is either a [Cloud Function](https://cloud.google.com/functions) or a [Cloud Run](https://cloud.google.com/run) instance, however all services are defined as web services that respond to HTTP JSON requests.

Most services do not allow unauthenticated requests. Services largely communicate with each other via [PubSub](https://cloud.google.com/pubsub/) messages.

See the README for a specific service for more details. See the [Services](#services) section for a list of services.

## Data Model

> :construction: Todo: Replace this section with easy graphic and then link to detailed document with this information.

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

Data is stored in [Google Firestore](https://firebase.google.com/docs/firestore) database with a flat structure:

```md
# Data Storage
images
observations
units
processed_observations
lightcurves
```

<a href="#" id="data-input"></a>

| collection               | key           | key example                     | description                                                                               |
| ------------------------ | ------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |
| `images`                 | `image_id`    | `PAN012_95cdbc_20191025T023434` | A single image at a set exposure.                                                         |
| `observations`           | `sequence_id` | `PAN012_95cdbc_20191025T023224` | A sequence of images defined by a mount slew.                                             |
| `units`                  | `unit_id`     | `PAN001`                        | Data for a given PANOPTES unit.                                                           |
| `processed_observations` | [generated*]  | `8zPAXSech07URES7WuTz`          | Metadata about a processed observation. Each observation may be processed multiple times. |
| `lightcurves`            | [generated*]  | `P2t4GGYpkByRqAabWqhe`          | Generated lightcurve data from a single processing run.                                   |

### Data Descriptions
<a href="#" id="data-descriptions"></a>

> :warning: Note: PANOPTES data is stored in [Firestore](https://firebase.google.com/docs/firestore), which is a NoSQL database.
Unlike a traditional database, this means that there is no guarantee that a certain field will be present. As part of our processing we try to guarantee that the fields listed below are always present, however the document may also contain additional fields not documented here.

#### Unit

Collection: `units`
Document ID: `unit_id`

```py
{
    "PAN001": {
        "name": "PAN001",
        "elevation": 3400.0,      # meters
        "location": {             # stored as GeoPoint
            "latitude": 19.54,    # degrees
            "longitude": -155.58  # degrees
        },
        "status": "active"
    }
}
```

#### Observation

An observation is a sequence of images from a single camera taken from a single unit during one continuous
tracking movement. Any movement of the mount (e.g. a meridian flip) will stop the current observation, even if
the same target is observed next. Ideally a unit will have at least two simulataneous observations at any
given time (one for each camera).

Observations are organized by a `sequence_id` of the form:

`<UNIT_ID>_<CAMERA_ID>_<SEQUENCE_START_TIME>`.

Collection: `observations`
Document ID: `sequence_id`
Notes:

  * An observation will always have `ra` and `dec` columns but the values may be `null`. Typically this indicates the file has not been properly plate-solved.

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
        "time": DatetimeWithNanoseconds(2018, 2, 16, 11, 6, 23, tzinfo=<UTC>)
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
    "ha_mnt": 1.919988307895942,       # From the mount
    "ra_mnt": 133.1505416666667,       # From the mount
    "dec_mnt": 28.33138888888889,      # From the mount
    "ra_image": 135.884026231,         # From plate solve
    "dec_image": 28.3746828541,        # From plate solve
    "exptime": 120,
    "moonfrac": 0.003716693699630014,
    "moonsep": 21.88964559220797,
    "airmass": 1.126544582361047,
    "bucket_path": "PAN001/14d3bd/20180216T110623/20180216T112430.fits.fz",
    "sequence_id": "PAN001_14d3bd_20180216T110623",
    "status": "uploaded",
    "time": DatetimeWithNanoseconds(2018, 2, 16, 11, 24, 30, tzinfo=<UTC>)
  }
}
```

#### Star

_coming soon..._

#### Lightcurve

_coming soon..._

## Data Explorer

The Data Explorer is a web-based tool to explore PANOPTES data at the observation and lightcurve level.

See [Data Explorer README](data-explorer/README.md) for details.

## Services
<a href="#" id="services"></a>

There are a few different categories of services that are in use on the panoptes-network.

| Service                                        | Trigger | Description                                                     |
| ---------------------------------------------- | ------- | --------------------------------------------------------------- |
| [`image-uploaded`](image-uploaded/README.md)   | Bucket  | Simple foward to next service based on file type.               |
| [`compress-fits`](compress-fits/README.md)     | PubSub  | Compresses all `.fits` to `.fits.fz`.                           |
| [`make-rgb-fits`](make-rgb-fits/README.md)     | PubSub  | Makes interpolated RGB `.fits` from `.CR2` file.                |
| [`record-image`](record-image/README.md)       | PubSub  | Records header and metadata from `.fits.fz` files.              |
| [`lookup-field`](lookup-field/README.md)       | Http    | A simple service to lookup astronomical sources by search term. |
| [`get-fits-header`](get-fits-header/README.md) | Http    | Returns the FITS headers for a given file.                      |

### Deploying services
<a href="#" id="deploying-services"></a>
<a href="#" id="deploy"></a>

You can deploy any service using `bin/deploy` from the top level directory. The
command takes the service name as a parameter:

```bash
$ bin/deploy record-image
```
### Creating new services

> Todo: More here.

Services are either written in Python or JavaScript.

See https://github.com/firebase/functions-samples

## Development

Development within the `panoptes-network` repository could be related to either the updating of individual GCP services or could be related to [Data Explorer](#data-explorer).

For the individual services the work is usually constrained to a single service/folder within this repository and the changes can be published according to the [Deploying services](#deploying-services) section above.

For instructions on working with the Data Explorer, see the [Development section](data-explorer#data-explorer/README.md) of the README.

### Setup

You must first have an environment that has the approriate software installed.

The easiest way to do this with an [Anaconda](https://www.anaconda.com/) environment. Assuming you already have `conda` installed (see link for details):

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
