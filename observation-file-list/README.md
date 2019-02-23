Get Observations Data
=====================

Type: [Google Cloud Function](https://cloud.google.com/functions/)
Purpose: Generate a downloadable text file that can be used by wget or curl to download the observation images.
Name: observation-file-list
Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/get-observations-data
Payload Example: 

	```
	{ "header": fits_header }
	```

TODO:

	* Add support for different file types.

Environment Variables:

	:warning: You must set the environment varibales via the web interface.

	POSTGRES_PASSWORD: Password for the metadata database.


## Deployment

> See also: [Offical Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

The is a convenience script to help deploy:

```bash
# Deploy function from current directory
./deploy.sh
```