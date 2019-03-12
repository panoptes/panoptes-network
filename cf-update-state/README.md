Add FITS Header to Database
===========================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

Small helper function to update the `state` column on either a sequence or an
image in the `metadata` db.


Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/header-to-db

Payload: JSON message of the form: 
	```json
	{ 
		'header': dict,
		'lookup_file': str,
	}
	```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `header-to-db`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 header-to-db \
                 --entry-point header_to_db \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing. 
```bash
./deploy.sh
```