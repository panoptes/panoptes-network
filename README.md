# PANOPTES Network

Software related to the wider PANOPTES network that ties the individual units together.
This is a repository to host the various Google Cloud Environment techonologies,
such as the Cloud Funcitions (CF) and any AppEngine definitions.

Each subfolder defines a different serivce and the services should be used from
their respective directories. Each directory has a specific README.

Services are prefixed with the technology they use:

`cf`: cloud function
`gce`: Google compute engine
`kube`: Kuberentes cluster

## Pipeline

Any image that is uploaded to the Google storage bucket will automatically trigger
the pipeline and cause a series of basic cleaning and reduction steps to happen.

The services defined in this repo control the different "nodes" of the pipeline,
which is currently spread across a variety of technologies.

### Receive Image

Images are uploaded into a google bucket. Alternatively a message can be sent directly
to the `cf-image-received` endpoint.

#### Bucket Upload

**Service:** `cf-bucket-upload`
[README](cf-bucket-upload/README.md)

A cloud function that receives a message each time an image (CR2 or FITS) is upload.
Simply forwards the request on to the `cf-image-received` service.

#### Image Received

**Service:** `cf-image-received`
[README](cf-image-received/README.md)

Triggers an action depending on the image type. If a FITS image, send to `cf-header-to-db`
to read the FITS headers into a metadatabase. If CR2, convert to FITS (todo), make timelapse (todo),
make jpgs for display (todo), and make separate RGB fits files for processing. 

### Process Image

#### CR2

Processing done for Canon CR2 images.

##### FITS

Todo - Currently done on units.

##### RGB FITS

**Service:** `cf-make-rgb-fits`
[README](cf-make-rgb-fits/README.md)

Create separate FITS images for each of the color channels. These images are interpolated 
and should not be used for science but can be used for image processing.

##### Timelapse

Todo - Currently done on units.

##### Pretty images

Todo - Currently done on units.

#### FITS

##### Headers

**Service:** `cf-header-to-db`
[README](cf-header-to-db/README.md)

The FITS headers are read from each file and added to the Cloud SQL `panoptes-meta.metadata`
database.

After successful reading of FITS headers the image is forwarded to the `gce-plate-solver` via
a PubSub message.

##### Plate Solve & Source Extraction
**Service:** `gce-plate-solver`
[README](gce-plate-solver/README.md)

Listens for PubSub messages on the `gce-plate-solver` subscription and for each received
file will attempt to:

1. Download the image from the storage bucket.
2. Plate-solve the field with astrometry.net.
3. Upload newly solved file back to storage bucket.
4. Perform source extraction with `sextractor`.
5. Do a catalog match with the detected sources and the TESS catalog.
6. Generate data stamps for each of the detected and matched sources and add to Cloud SQL database.

## POE - PANOPTES Observations Explorer
<a id="observations-explorer"></a>

A simple table display of the Observations. This reads JSON files that are provided
via the [Observations Data CF](#observations-data)

See [README](observations-explorer/README.md).

## Observations Data
<a id="observatons-data"></a>

A JSON service for the observations data.

See [README](observations-data/README.md).
