Add FITS Header to Database
===========================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/)
that can be used to up add FITS header information to a Cloud SQL database.

Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/header-to-metadb

Payload: JSON message of the form: 
	```json
	{ 'header': fits_header }
	```

Deploy
------

Documentation: https://cloud.google.com/functions/docs/deploying/filesystem

From the directory containing the cloud function:

```bash
gcloud functions deploy header-to-metadb --entry-point header_to_db --runtime python37 --trigger-http

```