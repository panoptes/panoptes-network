Make separate RGB FITS files
============================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will take a raw CR2 file and split into three separate FITS files,
one for each color channel.

This endpoint looks for one parameter, `bucket_path`, which is the full path (minus)
the bucket name) to the stored CR2 file. Additionally, the parameter `rawpy_options`
can be passed that affects how the images are converted.

> :memo: Todo: Add `rawpy_options` documentation and examples.


Endpoint: /make-rgb-fits

Payload: JSON message of the form:
```json
{
	'bucket_path': str,
	'rawpy_options': dict,
}
```

Deploy
------

> :bulb: **See [Deployment](../README.md#deploy) in main README for preferred deployment method.**

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `make-rgb-fits`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 make-rgb-fits \
                 --entry-point entry_point \
                 --runtime python37 \
                 --trigger-http
```

