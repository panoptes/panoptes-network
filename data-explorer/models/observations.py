import pandas as pd

from bokeh.models import ColumnDataSource

from models.base import BaseModel


class Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__('observations', *args, **kwargs)

    def make_datasource(self, query_fn=None, limit=100, *args, **kwargs):
        """Make the datasource.

        By default this will pull the most recent observations. You can pass a
        `query_fn` callable that has a `google.cloud.firestore.collection.CollectionReference`
        as the first and only parameter.  This function should return a
        `google.cloud.firestore.query.Query` instance.

        Args:
            query_fn (callable|None, optional): A callable function to get the data from the collection. See description for details.
            limit (int, optional): Limit the number of documents, default 100.
            *args: Description
            **kwargs: Description
        """
        # Default search for recent documents.
        if query_fn is None:
            self.query_object = self.collection \
                .order_by('time', direction='DESCENDING').limit(limit)
        else:
            self.query_object = query_fn(self.collection)

        # Collect all the documents.
        data_rows = [
            dict(sequence_id=d.id, **d.to_dict())
            for d
            in self.query_object.stream()
        ]
        data_frame = pd.DataFrame(data_rows).fillna({'num_images': 0})
        self.data_source = ColumnDataSource(data_frame)

        # Set an initial index.
        # self.data_source.selected.indices = [0]

        return self

    def get_document(self, sequence_id, force=False):
        """Returns a specific document given by the sequence_id

        Args:
            sequence_id (str): A valid sequence ID.
            force (bool, optional): Document is only looked up once per
                `sequence_id` unless force=True, default False.
        """
        assert sequence_id is not None
        if sequence_id != self._sequence_id or force:
            obs_doc_ref = self.collection.document(sequence_id)
            obs_doc_snap = obs_doc_ref.get()
            data_rows = obs_doc_snap.to_dict()
            data_rows['sequence_id'] = sequence_id

            self.data_frame = pd.DataFrame(data_rows, index=[0])
            self.data_source = ColumnDataSource(self.data_frame)
            self._sequence_id = sequence_id
            self.data_source.selected.indices = [0]
