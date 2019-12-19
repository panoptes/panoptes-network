PIAA Details
============

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function returns information about a PIAA processing run. It is intended to
be consumed by the PICID Explorer.

The function expects a single parameter, called `document_id`, that corresponds to
the Firestore document id for the particular PICID source run.

Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/piaa-details

Payload: JSON message of the form:
	```json
	{
		'document_id': str,
	}
	```

Example
-------

Using [httpie](https://httpie.org/):

```bash
http https://us-central1-panoptes-survey.cloudfunctions.net/piaa-details \
	document_id=VwbDCkjX3THXf4VJQygT

```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `get-piaa-details`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 get-piaa-details \
                 --entry-point get_piaa_details \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing. This is the preferred deployment method.
```bash
./deploy.sh
```
