# Raw file uploaded

This service is triggered when a file is placed in our [Storage Bucket](https://cloud.google.com/storage/) (see also the
documentation about using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

The service will receive a PubSub message in a json format. Based on the file type that was uploaded various actions
will be taken:

FITS: Record metadata and move FITS file to `panoptes-raw-images` bucket. Also places a copy in `panoptes-archive`.

CR2: Forward to the `make-rgb-fits` service. Move to `panoptes-images-raw` bucket.

JPG: No further processing. Move to `panoptes-images-jpgs`.

MP4: Timelapse files are moved to the `panoptes-timelapse` bucket.

Other: All other files are moved to the `panoptes-images-temp` bucket as they shouldn't be placed in the raw bucket.

Additionally, the function will look for legacy files that have a `field_name` component to their path. This path will
be stripped and the file will be re-uploaded (and processed).

Endpoint: No public endpoint

#### Notification Creation

The bucket notification only needs to be created once, which can be done with the following command:

```sh
gsutil notification create -t raw-file-uploaded -f json -e OBJECT_FINALIZE gs://panoptes-images-incoming/
```

You can list existing notifications with:

```sh
gsutil notification list gs://panoptes-images-incoming/
```

# Make observation list

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will compile a list of all available observations, along with their plate-solved RA/Dec coordinates (for
the center of the image).

This list can easily be used to search for multiple matching observations based on coordinates, time, and/or unit_id.

This Cloud Function is called periodically by the Cloud Scheduler.

Endpoint: `/get-observation-list`

Output: https://storage.googleapis.com/panoptes-exp.appspot.com/observations.csv

Example usage:

```python
import pandas as pd

url = 'https://storage.googleapis.com/panoptes-exp.appspot.com/observations.csv'

observations_df = pd.read_csv(url)
```

# Get FITS header

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to lookup the FITS header from a file in the storage bucket.

This endpoint looks for one parameters, `bucket_path`. If
`bucket_path` is present then the header information will be pulled from the file and returned as a json document.

Endpoint: `/get-fits-header`

Payload:
JSON message of the form:

```json
{
  bucket_path: <str>
}
```

Response:

The JSON response will contain the `success` flag as well as the FITS headers as key/value pairs.

```json
{
  success: <bool>,
  header: {
    <FITSHEAD>: <any>
  }
}
```

# Make RGB FITS

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will take a raw CR2 file and split into three separate FITS files, one for each color channel.

This endpoint looks for one parameter, `bucket_path`, which is the full path (minus)
the bucket name) to the stored CR2 file. Additionally, the parameter `rawpy_options`
can be passed that affects how the images are converted.

> :memo: Todo: Add `rawpy_options` documentation and examples.


Endpoint: /make-rgb-fits

Payload: JSON message of the form:

```json
{
  'bucket_path': <str>,
  'rawpy_options': <dict>
}
```

# Get stats

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will compile the `stats` collection into a csv file. This function is called periodically by the cloud
scheduler and should not need to be called manually.

Endpoint: `/get-stats`

Output: https://storage.googleapis.com/panoptes-exp.appspot.com/stats.csv

Example usage (typically indexed by `Week` and `Unit`):

```python
import pandas as pd

url = 'https://storage.googleapis.com/panoptes-exp.appspot.com/stats.csv'
stats_df
pd.read_csv(url).sort_values(by=['Week', 'Unit']).set_index(['Week'])

stats_df.head()
```

|   Week | Unit   |   Images |   Observations |   Total Minutes |   Total Hours |   Year |
|-------:|:-------|---------:|---------------:|----------------:|--------------:|-------:|
|      1 | PAN001 |        0 |              0 |               0 |          0    |   2018 |
|      1 | PAN001 |        0 |              0 |               0 |          0    |   2019 |
|      1 | PAN001 |      226 |              4 |             452 |          7.53 |   2017 |
|      1 | PAN001 |     2290 |             37 |            2290 |         38.17 |   2020 |
|      1 | PAN008 |        0 |              0 |               0 |          0    |   2019 |

# Firestore stats updater

This folder defines some Cloud Functions that are automatically triggered any time `observations` or `images` firestore
records are added or removed.

This is used as a simple aggregator, with results stored in the `stats` collection.
