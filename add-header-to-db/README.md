Add FITS Header to Database
===========================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/)
that can be used to add FITS header information to the meta database, which itself is a [Cloud SQL Instanct](https://cloud.google.com/sql/docs/).	

Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/header-to-metadb

Payload: JSON message of the form: 
	```json
	{ 'header': dict }
	```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `header-to-metadb`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 header-to-metadb \
                 --entry-point header_to_db \
                 --runtime python37 \
                 --trigger-http
```