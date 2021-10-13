import os

import pandas as pd
from flask import jsonify
from google.cloud import firestore
from google.cloud import storage

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-exp.appspot.com')

storage_client: storage.Client = storage.Client()
output_bucket: storage.Bucket = storage_client.bucket(BUCKET_NAME)
firestore_db: firestore.Client = firestore.Client()


def entry_point(request):
    # Get the observation subcollection for each unit.
    field_obs = list()
    for unit_ref in firestore_db.collection('units').stream():
        obs = [d.to_dict() for d in
               firestore_db.collection(f'units/{unit_ref.id}/observations').stream()]
        field_obs.append(pd.json_normalize(obs, sep='_'))

    field_obs = pd.concat(field_obs)

    # Drop those missing time field.
    field_obs.dropna(subset=['time'], inplace=True)

    # Set up the date field.
    field_obs.time = pd.to_datetime(field_obs.time, utc=True)

    # Set time as index and sort.
    field_obs.set_index(['time'], inplace=True)
    field_obs.sort_index(ascending=False, inplace=True)

    # Change column types.
    field_obs.status = pd.Categorical(field_obs.status)
    field_obs.unit_id = pd.Categorical(field_obs.unit_id)

    # Correct bad name of unit.
    field_obs.loc[
        field_obs.unit_id == 'Panoptes Unit PAN006 @ Wheaton College', 'unit_id'] = 'PAN006'

    # Write to a CSV file object directly to bucket.
    csv_blob = output_bucket.blob('observations.csv')
    csv_blob.upload_from_string(field_obs.to_csv(), content_type='text/csv')
    csv_blob.make_public()

    # Write out to json as well.
    json_blob = output_bucket.blob('observations.json')
    json_blob.upload_from_string(field_obs.to_json(orient='records'),
                                 content_type='application/json')
    json_blob.make_public()

    return jsonify(success=True, public_url=[csv_blob.public_url, json_blob.public_url])
