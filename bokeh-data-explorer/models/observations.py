import pandas as pd

from bokeh.models import ColumnDataSource

from models.base import BaseModel


class Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sequence_id = None
        self._recent_docs = None

    def get_recent(self, limit=100):
        obs_query = self.collection.order_by('time', direction='DESCENDING').limit(limit)
        data_rows = [
            dict(sequence_id=d.id, **d.to_dict())
            for d
            in obs_query.stream()
        ]
        self.data_frame = pd.DataFrame(data_rows)
        self.data_source = ColumnDataSource(self.data_frame)

    def get_document(self, sequence_id):
        assert sequence_id is not None
        if sequence_id != self._sequence_id:
            obs_doc_ref = self.collection.document(sequence_id)
            obs_doc_snap = obs_doc_ref.get()
            data_rows = obs_doc_snap.to_dict()
            data_rows['sequence_id'] = sequence_id

            self.data_frame = pd.DataFrame(data_rows, index=[0])
            self.data_source = ColumnDataSource(self.data_frame)
            self._sequence_id = sequence_id
