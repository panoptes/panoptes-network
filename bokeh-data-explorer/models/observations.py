import pandas as pd

from bokeh.models import ColumnDataSource

from models.base import BaseModel


class Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sequence_id = None
        self._recent_docs = None

    def get_recent(self, limit=100):
        """Get the recent observation documents.

        Builds a DataFrame and ColumnDataSource for the collection.

        Args:
            limit (int, optional): Limit returned number of documents, default 100.
        """
        obs_query = self.collection.order_by('time', direction='DESCENDING').limit(limit)
        data_rows = [
            dict(sequence_id=d.id, **d.to_dict())
            for d
            in obs_query.stream()
        ]
        self.data_frame = pd.DataFrame(data_rows).fillna({'num_images': 0})
        self.data_source = ColumnDataSource(self.data_frame)
        self.data_source.selected.indices = [0]

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
