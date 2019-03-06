Make separate RGB FITS files
============================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will take a raw CR2 file and split into three separate FITS files,
one for each color channel.

This endpoint looks for one parameter, `cr2_file`, which is the full path (minus)
the bucket name) to the stored CR2 file. Additionally, the parameter `rawpy_options`
can be passed that affects how the images are converted. 

> :memo: Todo: Add `rawpy_options` documentation and examples.


Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/make-rgb-fits

Payload: JSON message of the form: 
	```json
	{ 
		'cr2_file': str,
		'rawpy_options': dict,
	}
	```

Example
-------

Using [httpie](https://httpie.org/):

```bash
http https://us-central1-panoptes-survey.cloudfunctions.net/make-rgb-fits \
	cr2_file=PAN001/46Pwirtanen/14d3bd/20181216T075740/20181216T080457.cr2

```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `header-to-metadb`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 make-rgb-fits \
                 --entry-point make_rgb_fits \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing. This is the preferred deployment method.
```bash
./deploy.sh
```