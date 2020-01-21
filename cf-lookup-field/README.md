Lookup Field
============

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This is essentially a thin-wrapper around `astropy.coordinates.SkyCoord.from_name`.

Endpoint: https://us-central1-panoptes-exp.cloudfunctions.net/lookup-field

Payload: JSON message of the form:
	```json
	{
		'search_string': str,
	}
	```

Example
-------

Using [httpie](https://httpie.org/):

```bash
http https://us-central1-panoptes-exp.cloudfunctions.net/lookup-field \
	search_string="m42"

```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `lookup-field`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 lookup-field \
                 --entry-point lookup_field \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing. This is the preferred deployment method.
```bash
./deploy.sh
```
