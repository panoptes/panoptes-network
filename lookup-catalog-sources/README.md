Lookup Catalog Sources
======================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to look up stellar sources from the PANOPTES catalog.

This endpoint looks for one parameter, `bucket_path`. If `bucket_path` is present 
then the World Coordinate System (WCS) from the solved image will be used to look
up the catalog sources for the entire observation. The matching sources, along with
the corresponding XY-pixel positions for the image, are saved back to the processing
bucket to be used for source extraction.


Endpoint: `/lookup-catalog-sources`

Payload: 
JSON message of the form:

```json
{
  bucket_path: str,
}
```

Response:

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
