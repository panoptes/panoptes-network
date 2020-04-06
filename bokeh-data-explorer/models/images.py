from bokeh.models import ColumnDataSource
from pandas import json_normalize

from models.base import BaseModel


class Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sequence_id = None

    def get_documents(self, sequence_id):
        assert sequence_id is not None
        if sequence_id != self._sequence_id:
            images_query = self.collection.where('sequence_id', '==', sequence_id)
            data_rows = [
                dict(image_id=d.id, **d.to_dict())
                for d
                in images_query.stream()
            ]
            self.data_frame = json_normalize(data_rows, sep='_')
            self.data_source = ColumnDataSource(self.data_frame)
            self._sequence_id = sequence_id
