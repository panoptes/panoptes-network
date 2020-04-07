import os
from google.cloud import firestore

project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'panoptes-exp')


class BaseModel:

    def __init__(self, collection_name):
        self.id = self.__module__
        self._firestore_db = firestore.Client(project=project_id)

        self.collection_name = collection_name
        self.collection = self._firestore_db.collection(self.collection_name)

        self.query_object = None
        self.data_source = None

    def make_datasource(self, *args, **kwargs):
        raise NotImplementedError

    def get_documents(self, *args, **kwargs):
        raise NotImplementedError
