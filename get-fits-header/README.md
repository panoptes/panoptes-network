Lookup FITS Header
==================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to lookup the FITS header from a file in the storage bucket.

This endpoint looks for one parameters, `bucket_path`. If
`bucket_path` is present then the header information will be pulled from the file
and returned as a json document.


Endpoint: `/get-fits-header`

Payload: 
JSON message of the form:

```json
{
	bucket_path: str,
}
```

Response:

The JSON response will contain the `success` flag as well as the FITS headers as key/value pairs.

```json
{
	success: <bool>,
	header: {
		<FITSHEAD>: <any>
	}
}
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
