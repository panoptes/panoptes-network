Plate Solver
------------

An astronomical-plate solving service that runs on a GCP Cloud Run cluster.

Input:

* `panoptes-images-calibrated` notification (see below).

Output:

* `panoptes-images-solved` for plate-solved FITS files.

### Deploy

The new service will be deployed automatically by Google Cloud Build.

### Notification Creation

The bucket notification only needs to be created once, which can be done with the following command:

```sh
gsutil notification create -t plate-solve -f json -e OBJECT_FINALIZE gs://panoptes-images-calibrated/
```

You can list existing notifications with:

```sh
gsutil notification list gs://panoptes-images-calibrated/
```
