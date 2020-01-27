Add FITS Header to Database
===========================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to add FITS header information to the meta database
(which itself is a [Cloud SQL Instanct](https://cloud.google.com/sql/docs/)).

This endpoint looks for two parameters, `headers` and `bucket_path`. If
`bucket_path` is present then the header information will be pull from the file
itself. Additionally, any `headers` will be used to update the header information
from the file. If no `bucket_path` is found then only the `headers` will be used.

> :memo: Todo: Document that explains overall structure.


Endpoint: `/header-to-db`

Payload: JSON message of the form:

```json
{
	'headers': dict,
	'bucket_path': str,
	'object_id': str,
}
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
