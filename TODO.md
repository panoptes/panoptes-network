Todo
----

* [ ] On `image-received`:
    * [x] `fits.fz`:
        * [ ] forward to `record-image`
    * [x] `fits`:
        * [ ] fpack the file, delete original `gcp-fits-packer`
    * [ ] `cr2`:
        * [ ] extract the jpg
        * [ ] convert to raw fits
        * [x] forward to `cf-make-rgb-fits`
    * [ ] other: move to different bucket?

* [x] On `cf-make-rgb-fits`:
    * [x] convert to 3 interpolated fits files for rgb
    * [x] uploaded fits files to `panoptes-rgb-images`

* [ ] On `record-image`:
    * [x] record image metadata in firestore.
    * [ ] Forward to `subtract-background`.

> _Unsure if we want the following services._

* [ ] On `subtract-background`:
    * [ ] subtract background.
        * [ ] save background to `panoptes-backgrounds`.
    * [ ] update image metadata.
    * [ ] forward to `plate-solve`.

* [ ] On `plate-solve`:
    * [ ] plate-solve.
        * [ ] save processed image to `panoptes-processed-images`.
    * [ ] update image metadata.


Todo regarding above:

* [ ] Process `fits` in `panoptes-raw-images`.
* [ ] Process `cr2` in `panoptes-raw-images`.

### Todo for export metadata observations:

* [ ] Find unsolved files in `panoptes-raw-images` and solve them.
    * [ ] Update `ra_image` and `dec_image` in images collection.
    * [ ] Change `status` to `solved`.

* [ ] Remove `camsn` from `images` collection.
* [ ] Remove `POINTING` keyword from `observations` with status `metadata_received`.

### Todo for processing:

* [ ] Add gaia dr2 id to document?


## With O & P:

* [ ] Extract `lookup_fits_header` from `cf-record-image` into separate cf.
* [ ] cf to update basic `observations` and `units` stats in firestore.
