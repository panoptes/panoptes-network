Lookup FITS Header
==================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to lookup the FITS header from a file in the storage bucket.

This endpoint looks for one parameters, `bucket_path`. If
`bucket_path` is present then the header information will be pulled from the file
and returned as a json document.


Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/get-fits-header

Payload: JSON message of the form:
	```json
	{
		'bucket_path': str,
	}
	```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `get-fits-header`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 get-fits-header \
                 --entry-point entry_point \
                 --runtime python37 \
                 --trigger-http
```

:bulb: There is also a small convenience script called `deploy.sh` that
does the same thing.
```bash
./deploy.sh
```
