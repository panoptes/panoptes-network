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


#### Notification Creation

The bucket notification only needs to be created once, which can be done with the following command:

```sh
gsutil notification create -t observation-file-uploaded -f json -e OBJECT_FINALIZE gs://panoptes-observations/
```

You can list existing notifications with:

```sh
gsutil notification list gs://panoptes-observations/
```
