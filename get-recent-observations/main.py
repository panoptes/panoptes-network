import os
from io import StringIO

import pandas as pd
import pendulum
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
    # TODO could pull these from request
    start_time = pendulum.now().subtract(months=1)
    doc_limit = 100
    output_filename = 'recent.csv'

    # Get the recent query.
    obs_query = firestore_db.collection('observations').where('received_time', '>=', start_time).limit(doc_limit)

    # Gather the documents.
    obs_docs = [{'sequence_id': d.id, **d.to_dict()} for d in obs_query.stream()]

    # Build the DataFrame.
    recent_df = pd.DataFrame(obs_docs).sort_values(by=['received_time'])

    # Write to a CSV file object.
    sio = StringIO()
    recent_df.to_csv(sio, index=False)
    sio.seek(0)

    # Upload file object to public blob.
    blob = output_bucket.blob(output_filename)
    blob.upload_from_file(sio)
    blob.make_public()

    return jsonify(success=True, public_url=blob.public_url)
