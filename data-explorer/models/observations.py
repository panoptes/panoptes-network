import holoviews as hv
import pandas as pd
from models.base import BaseModel


class Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__('observations', *args, **kwargs)

    def get_data(self, query_fn=None, limit=100, *args, **kwargs):
        """Make the datasource.

        By default this will pull the most recent observations. You can pass a
        `query_fn` callable that has a `google.cloud.firestore.collection.CollectionReference`
        as the first and only parameter.  This function should return a
        `google.cloud.firestore.query.Query` instance.

        Args:
            query_fn (callable|None, optional): A callable function to get the data from the
            collection. See description for details.
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
        self.table = hv.Table(pd.DataFrame(data_rows).fillna({'num_images': 0}))

        return self
