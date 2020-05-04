Lookup Catalog Sources
======================

This folder defines a [Google Cloud Platform](https://cloud.google.com/) service that responds
to a PubSub message on the `lookup-catalog-sources` topic.

This service is used to look up stellar sources from the PANOPTES catalog. The service works
on the observation level and so accepts `sequence_id` as its default parameter. Given a
`sequence_id`, the service will lookup the World Coordinate System (WCS) from images in the
observation sequence that have been successfully plate-solved.

Currently the service will just look for the first image in the series and use that as
the representative WCS.  To specify which file to use, pass either a `bucket_path` or
an `image_id` pointing to the specific image to use.

Once a WCS for the observation is determined, the service will look up the corresponding
sources in the catalog. By default there is a Vmag range of `[6,18)`. 

The matching sources, along with the corresponding XY-pixel positions for the image, 
are saved to the `panoptes-processed-observations` bucket to be used for source extraction.
By default the results are saved in Parquet format. Set a `format=csv` attribute for csv.

The results should primarily be accessed via BigQuery.  

Topic: `lookup-catalog-sources`  
Attributes:
  * `sequence_id`: The `sequence_id` of the observation to lookup. 
  * `image_id | bucket_path`: The `image_id` or `bucket_path` of the specific image 
    to use for the WCS lookup.


### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
