import os
from io import StringIO

import pandas as pd
from flask import jsonify
from google.cloud import firestore
from google.cloud import storage

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-exp.appspot.com')

storage_client = storage.Client()
output_bucket = storage_client.bucket(BUCKET_NAME)
firestore_db = firestore.Client()


# Entry point
def entry_point(request):
    output_filename = 'observations.csv'

    # Get the recent query.
    obs_query = firestore_db.collection('observations')

    # Gather the documents.
    obs_docs = [{'sequence_id': d.id, **d.to_dict()} for d in obs_query.stream()]

    # Build the DataFrame.
    recent_df = pd.DataFrame(obs_docs).sort_values(by=['time'])

    columns = [
        'unit_id',
        'time',
        'sequence_id',
        'image_id',
        'ra',
        'dec',
        'exptime',
        'field_name',
        'num_images',
        'iso',
        'total_minutes_exptime',
        'status',
        'software_version',
        'camera_id',
    ]

    recent_df = recent_df[columns]

    # Write to a CSV file object.
    sio = StringIO()
    recent_df.to_csv(sio, index=False)
    sio.seek(0)

    # Upload file object to public blob.
    blob = output_bucket.blob(output_filename)
    blob.upload_from_file(sio)
    blob.make_public()

    return jsonify(success=True, public_url=blob.public_url)
