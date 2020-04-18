import holoviews as hv
import pandas as pd
from astropy import units as u
from models.base import BaseModel


class Model(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__('stats', *args, **kwargs)

    def get_data(self, *args, **kwargs):
        """Fetch the stats.

        Args:
            *args: Description
            **kwargs: Description
        """
        # Collect all the documents.
        data_rows = list()
        for d in self.collection.where('year', '>=', 2018).stream():
            data_rows.append(d.to_dict())

        stats_df = pd.DataFrame(data_rows)

        # Get a real time column
        hours = (stats_df.total_minutes_exptime * u.minute).values.to(u.hour).value
        stats_df['total_hours_exptime'] = [round(x, 2) for x in hours]
        stats_df.index = pd.to_datetime(
            stats_df.year.astype(str) + stats_df.week.map(lambda x: f'{x:02d}') + ' SUN',
            format='%Y%W %a')

        # Reorder
        stats_df = stats_df.reindex(
            columns=['unit_id', 'week', 'year', 'num_images', 'num_observations',
                     'total_minutes_exptime', 'total_hours_exptime'])

        def reindex_by_date(df):
            dates = pd.date_range(df.index.min(), df.index.max(), freq='W')
            return df.reindex(dates).fillna(0)

        stats_df = stats_df.sort_index().groupby('unit_id').apply(reindex_by_date)
        stats_df = stats_df.droplevel('unit_id').reset_index().rename(columns={'index': 'date'})

        self.table = hv.Table(stats_df)

        return self
