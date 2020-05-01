import hvplot.pandas  # noqa
import pandas as pd  # noqa
import panel as pn
import param

from astropy import units as u

COLLECTION = 'stats'


class Stats(param.Parameterized):
    year = param.Selector()
    metric = param.Selector(default='Images')

    def __init__(self, firestore_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._firestore_db = firestore_client
        self.collection = self._firestore_db.collection(COLLECTION)
        self.df = None
        self.get_data()

        # Set some default for the params now that we have data.
        self.param.year.objects = sorted(self.df.Year.unique().tolist())
        self.year = 2020

        self.param.metric.objects = self.df.select_dtypes(include='float64').columns.tolist()
        self.metric = 'Total Hours'

    @param.depends('year', 'metric')
    def plot(self):
        self.get_data()
        year = self.year
        metric = self.metric
        df2 = self.df.query('Year == @year').copy()
        df2 = df2.reset_index().sort_values(by=['Unit', 'Week']).set_index(['Week'])
        title = '{} {}={}'.format(
            year,
            metric.title().replace('_', ' '),
            int(df2[metric].sum())
        )

        return df2.hvplot.bar(
            y=metric,
            stacked=True,
            by='Unit',
            title=title,
            rot=90
        )

    def widget_box(self):
        return pn.WidgetBox(
            pn.Param(
                self.param,
                widgets={
                    'year': pn.widgets.RadioButtonGroup,
                    'metric': pn.widgets.RadioBoxGroup,
                }
            ),
        )

    def get_data(self):
        # Get a real time column
        stats_rows = [d.to_dict()
                      for d
                      in self.collection.where('year', '>=', 2018).stream()]
        stats_df = pd.DataFrame(stats_rows)

        hours = (stats_df.total_minutes_exptime * u.minute).values.to(u.hour).value

        stats_df['total_hours_exptime'] = [round(x, 2)
                                           for x
                                           in hours]
        stats_df.index = pd.to_datetime(
            stats_df.year.astype(str) + stats_df.week.map(lambda x: f'{x:02d}') + ' SUN',
            format='%Y%W %a'
        )

        columns = {
            'unit_id': 'Unit',
            'week': 'Week',
            'year': 'Year',
            'num_images': 'Images',
            'num_observations': 'Observations',
            'total_minutes_exptime': 'Total Minutes',
            'total_hours_exptime': 'Total Hours'
        }

        # Reorder
        stats_df = stats_df.reindex(columns=list(columns.keys()))

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

        stats_df = stats_df.rename(columns=columns)
        stats_df = stats_df.reset_index(drop=True).set_index(['Week'])

        self.df = stats_df.sort_index()
