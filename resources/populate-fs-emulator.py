#!/usr/bin/env python3

import os
import click
import mock

from google.cloud import firestore
import google.auth.credentials

from panoptes.utils.serializers import from_json


@click.command()
@click.argument('data_path')
def main(data_path):
    print(f'Processing {data_path}')

    with open(data_path, 'r') as f:
        data = from_json(f.read())

    # Show basic stats
    print({k: len(v) for k, v in data.items()})

    # Get the database
    if os.getenv('GAE_ENV', '').startswith('standard'):
        # production
        db = firestore.Client()
    else:
        # localhost
        os.environ["FIRESTORE_DATASET"] = "panoptes-exp"
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
        os.environ["FIRESTORE_EMULATOR_HOST_PATH"] = "localhost:8080/firestore"
        os.environ["FIRESTORE_HOST"] = "http://localhost:8080"
        os.environ["FIRESTORE_PROJECT_ID"] = "panoptes-exp"

        credentials = mock.Mock(spec=google.auth.credentials.Credentials)
        db = firestore.Client(project="panoptes-exp", credentials=credentials)

    batch = db.batch()

    for collection_name, docs in data.items():
        print(
            f'Emulator: adding {len(docs)} docs to [{collection_name}] collection')
        col_ref = db.collection(collection_name)
        for doc_id, doc_data in docs.items():
            doc_ref = col_ref.document(doc_id)
            batch.create(doc_ref, doc_data)

    print(f'Commiting batch')
    batch.commit()

    print('Looking up record summary')
    print('Units: ', len([u.id for u in db.collection('units').stream()]))
    print('Obs:   ', len([u.id for u in db.collection('observations').stream()]))
    print('Images: ', len([u.id for u in db.collection('images').stream()]))


if __name__ == "__main__":
    main()
