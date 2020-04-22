from bokeh.models.widgets import DataTable
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import NumberFormatter
from bokeh.models.widgets import DateFormatter

import numpy as np
import holoviews as hv

from modules.base import BaseModule


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model, name=__name__)

    def make_plot(self):
        # self.data_table = DataTable(
        #     source=self.model.table,
        #     # selectable=True,
        #     # index_position=None,
        #     # fit_columns=True,
        #     columns=[
        #         TableColumn(
        #             field='unit_id',
        #             title='Unit',
        #             width=40,
        #         ),
        #         TableColumn(
        #             field='sequence_id',
        #             title='Observation ID',
        #             width=150,
        #         ),
        #         TableColumn(
        #             field='field_name',
        #             title='Field',
        #             width=150,
        #         ),
        #         TableColumn(
        #             field='ra',
        #             title='RA',
        #             formatter=NumberFormatter(format="0.00"),
        #             width=20,
        #         ),
        #         TableColumn(
        #             field='dec',
        #             title='Dec',
        #             formatter=NumberFormatter(format="0.00"),
        #             width=20,
        #         ),
        #         TableColumn(
        #             field='exptime',
        #             title='Exptime [sec]',
        #             formatter=NumberFormatter(format="0.00"),
        #             width=20,
        #         ),
        #         TableColumn(
        #             field='time',
        #             title='Date [UTC]',
        #             formatter=DateFormatter(format="%m/%d/%Y %H:%M"),
        #             width=70,
        #         ),
        #         TableColumn(
        #             field='num_images',
        #             title='Images',
        #             width=20,
        #         ),
        #         TableColumn(
        #             field='status',
        #             title='Status',
        #             width=20,
        #         ),
        #     ]
        # ).opts()

        columns = [
            'unit_id',
            'sequence_id',
            'field_name',
            'ra', 'dec',
            'exptime',
            'time',
            'num_images',
            'status'
        ]
        df0 = self.model.df[columns]

        return df0.hvplot.table(name='obs_recent_table')

    def update_plot(self, dataframe=None):
        pass

    def busy(self):
        pass

    def unbusy(self):
        pass
