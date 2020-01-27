Lookup Field
============

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is a thin-wrapper around [`astropy.coordinates.SkyCoord.from_name`](https://docs.astropy.org/en/stable/api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord.from_name).

Endpoint: `/lookup-field`

Payload: 
```json
{
	search_string: <str>,
}
```

Response:
```json
{
	ra: <float>,
	dec: <float>,
	search_string: <str>,
	success: <bool>,
}
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
