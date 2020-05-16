import os

import hvplot.pandas  # noqa
import pandas as pd  # noqa
import panel as pn
import param
from astropy.utils.data import download_file
from panoptes.utils.logger import logger

logger.enable('panoptes')

BASE_URL = os.getenv('BASE_URL', 'https://storage.googleapis.com/panoptes-exp.appspot.com/stats.csv')


class Stats(param.Parameterized):
    year = param.Selector()
    metric = param.Selector(default='Images')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stats_path = None
        self.df = None
        self.get_data()

        # Set some default for the params now that we have data.
        self.param.year.objects = [2016, 2017, 2018, 2019, 2020]
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
        logger.debug(f'Getting recent stats from {BASE_URL}')
        self._stats_path = download_file(f'{BASE_URL}',
                                         cache='update',
                                         show_progress=False,
                                         pkgname='panoptes')
        stats_df = pd.read_csv(self._stats_path).convert_dtypes(convert_integer=False)

        self.df = stats_df.sort_index()
