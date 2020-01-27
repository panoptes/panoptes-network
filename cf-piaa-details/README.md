PIAA Details
============

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function returns information about a PIAA processing run. It is intended to
be consumed by the Data Explorer but could also be used as a generic API endpoint.

The function expects a single parameter, called `document_id`, that corresponds to
the Firestore document id for the particular PICID source run.

Endpoint: `/piaa-details`

Payload: 

JSON message of the form:
```json
{
	document_id: <str>,
}
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
