Get Sequence/Image State
========================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

Small helper function to update the `state` column on either a sequence or an
image in the `metadata.observations` db.

Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/update-observation-state

Can be passed either a `sequence_id` or an `image_id`.

Payload: JSON message of the form:

```json
{
    'state': str,
    'sequence_id': str,
    'image_id': str
}
```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `update-observation-state`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 update-observation-state \
                 --entry-point update_state \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing.
```bash
./deploy.sh
```
