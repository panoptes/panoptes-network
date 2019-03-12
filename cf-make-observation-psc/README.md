Make Observation PSC
====================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function will make a single CSV file that contains all the individual postage
stamps for a given observation sequence. The individual images are created as part
of the `gce-plate-solver` and are placed in the `panoptes-detected-sources` bucket.

Here we look for all the files in `gs://panoptes-detected-sources/{sequence_id}.csv`

This endpoint looks for one parameter, `sequence_id`, which is the full path (minus)
the bucket name) to the CSV files for each observation sequences. 

Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/make-observation-psc

Payload: JSON message of the form: 
	```json
	{ 
		'sequence_id': str,
	}
	```

Example
-------

Using [httpie](https://httpie.org/):

```bash
http https://us-central1-panoptes-survey.cloudfunctions.net/make-observation-psc \
	sequence_id=PAN001/14d3bd/20181216T075740

```

Deploy
------

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing. This is the preferred deployment method.
```bash
./deploy.sh
```

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `make-observation-psc`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 make-observation-psc \
                 --entry-point make_observation_psc \
                 --runtime python37 \
                 --trigger-http
```
