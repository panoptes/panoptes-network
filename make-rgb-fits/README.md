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
```javascript
{
	'bucket_path': str,
	'rawpy_options': dict,
}
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
