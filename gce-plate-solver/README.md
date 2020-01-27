# Plate Solver

This folder creates a number of services related to plate-solving astronomical
images. It is designed to be run as a Flask service inside a Docker container
that is run on a Google Cloud Engine instance.

* **app.py**: Flask service the defines two endpoints:
	* `/solve`:
		* __params__: 
			`filename`: A string that specifies the path to the FITS file as
			it is stored in the Google storage bucket. The path should not include
			the name of the bucket.
		* __returns__:
			`status`: "sources_extracted"
			`filename`: The name that will be used to store the plate-solved FITS
			file in the storage bucket. This is most likely the same as the input
			`filename` param although could change (e.g. if input is not compressed).

		The `solve` routine perform the following steps:

			1. Download the FITS `filename` from the storage bucket.
			2. Unpack the compressed FITS file.
			3. Plate-solve the field.
			4. Lookup point sources in the field using `sextractor`.
			5. Catalog match the detected sources with the PANOPTES Input Catalog.
			6. Send matched source information to BigQuery table.
			7. Upload plate-solved FITS file.
			8. Return `sources_extracted` status.
* **Dockerfile**: Defines a simple Docker image based off the `PIAA` base image.
	The Docker container runs `start.sh`.
* **start.sh**: Start the Google Cloud SQL proxy script and a [Gunicorn](https://gunicorn.org/) server running
	the Flask service defined in `app.py`.
* **wsgi.py**: Used by `gunicorn` to help start the Flask service.

You can make requests from the service with a JSON POST:
```
import requests

url = 'http://127.0.0.1:8080/solve'  # Replace with real url
remote_path = 'PAN001/Tess_Sec09_Cam01/ee04d1/20190222T085905/20190222T091336.fits.fz'

res = requests.post(url, json={ 'filename': remote_path })
```
