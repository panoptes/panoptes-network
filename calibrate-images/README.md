Calibrate FITS Files
====================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to calibrate the FITS images, which consists of the following steps:

1. Subtract zero-level camera bias of `2048 ADU`.
2. Calculate and remove global RGB background.

The background subtraction is calculated separately for each of the color channels and saved to a
separate FITS file. The original FITS file is not altered.

Input:

* `panoptes-images-raw` notification (see below).

Output:

* `panoptes-images-calibrated` for reduced FITS images.
* `panoptes-images-backgrounds` for RGB background file.

### Deploy

```shell
# Run from current directory.
./deploy.sh
```

### Notification Creation

The bucket notification only needs to be created once, which can be done with the following command:

```sh
gsutil notification create -t calibrate-images -f json -e OBJECT_FINALIZE gs://panoptes-images-raw/
```

You can list existing notifications with:

```sh
gsutil notification list gs://panoptes-images-raw/
```
