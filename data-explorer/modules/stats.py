import param
import pandas as pd
import hvplot.pandas  # noqa

from astropy import units as u

COLLECTION = 'stats'


class Stats(param.Parameterized):
    year = param.Selector()
    metric = param.Selector(default='num_images')

    def __init__(self, firestore_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._firestore_db = firestore_client
        self.collection = self._firestore_db.collection(COLLECTION)
        self.get_data(*args, **kwargs)

        # Set some default for the params now that we have data.
        self.param.year.objects = sorted(self.df.year.unique().tolist())
        self.year = 2020

        self.param.metric.objects = self.df.select_dtypes(include='float64').columns.tolist()
        self.metric = 'total_hours_exptime'

    @param.depends('year', 'metric')
    def plot(self):
        self.get_data()
        year = self.year
        metric = self.metric
        df2 = self.df.query('year == @year').copy()
        df2 = df2.reset_index().sort_values(by=['unit_id', 'week']).set_index(['week'])
        title = '{} {}={}'.format(
            year,
            metric.title().replace('_', ' '),
            int(df2[metric].sum())
        )

        return df2.hvplot.bar(
            y=metric,
            stacked=True,
            by='unit_id',
            title=title,
            rot=90
        )

    def get_data(self):
        # Get a real time column
        try:
            stats_df = pd.read_csv('stats.csv')
        except FileNotFoundError:
            stats_rows = [d.to_dict()
                          for d
                          in self.collection.where('year', '>=', 2018).stream()]
            stats_df = pd.DataFrame(stats_rows)
            stats_df.to_csv('stats.csv')

        hours = (stats_df.total_minutes_exptime * u.minute).values.to(u.hour).value

        stats_df['total_hours_exptime'] = [round(x, 2)
                                           for x
                                           in hours]
        stats_df.index = pd.to_datetime(
            stats_df.year.astype(str) + stats_df.week.map(lambda x: f'{x:02d}') + ' SUN',
            format='%Y%W %a'
        )

        columns = [
            'unit_id',
            'week',
            'year',
            'num_images',
            'num_observations',
            'total_minutes_exptime',
            'total_hours_exptime'
        ]

        # Reorder
        stats_df = stats_df.reindex(columns=columns)

        stats_df.sort_index(inplace=True)
        stats_df.drop(columns=['week', 'year'], inplace=True)

        def reindex_by_date(group):
            dates = pd.date_range(group.index.min(), group.index.max(), freq='W')
            unit_id = group.iloc[0].unit_id
            group = group.reindex(dates).fillna(0)
            group.unit_id = unit_id

            return group

        stats_df = stats_df.groupby(['unit_id']).apply(reindex_by_date).droplevel(0)

        stats_df['year'] = stats_df.index.year
        stats_df['week'] = stats_df.index.week
        stats_df = stats_df.reset_index(drop=True).set_index(['week'])

        self.df = stats_df.sort_index()
