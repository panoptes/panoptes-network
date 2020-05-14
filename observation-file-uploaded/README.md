Observations File Uploaded
==========================

This service is triggered  when a file is placed in our [Storage Bucket](https://cloud.google.com/storage/)
(see also the documentation about using [Storage Triggers](https://cloud.google.com/functions/docs/calling/storage)).

The service will receive a PubSub message in a json format. The file will either be
an observations metadata file (information about the images within the observation),
or source information (a catalog lookup of the sources in the FOV).

Endpoint: No public endpoint

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.

### Setup

The following steps were performed to help set up the Cloud Function and should not need
to be performed again.

#### BigQuery Tables

The BigQuery tables are created via a json schema located in the resources folder.

These tables were created via:

```bash
bq mk \
--table \
--description "Image level metadata for each observation." \
observations.metadata \
/var/panoptes/panoptes-network/resources/observations.metadata-schema.json

bq mk \
--table \
--description "Catalog sources for a given observation." \
observations.sources \
/var/panoptes/panoptes-network/resources/observations.sources-schema.json
```


#### Notification Creation

The bucket notification only needs to be created once, which can be done with the following command:

```sh
gsutil notification create -t observation-file-uploaded -f json -e OBJECT_FINALIZE gs://panoptes-observations/
```

You can list existing notifications with:

```sh
gsutil notification list gs://panoptes-observations/
```
