from bokeh.models.widgets import DataTable
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import NumberFormatter
from bokeh.models.widgets import DateFormatter
from bokeh.models import Panel
from bokeh.layouts import column

from modules.base import BaseModule


TITLE = ''


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model)

    def make_plot(self):
        column_width = 1000  # pixels

        self.data_table = DataTable(source=self.model.data_source,
                                    name='recent_observations_table',
                                    width=column_width,
                                    index_position=None,
                                    columns=[
                                        TableColumn(
                                            field='unit_id',
                                            title='Unit',
                                            width=5),
                                        TableColumn(
                                            field='sequence_id',
                                            title='Observation ID',
                                            width=80),
                                        TableColumn(
                                            field='field_name',
                                            title='Field',
                                            width=80),
                                        TableColumn(
                                            field='ra',
                                            title='RA',
                                            formatter=NumberFormatter(format="0.00"),
                                            width=10),
                                        TableColumn(
                                            field='dec',
                                            title='Dec',
                                            formatter=NumberFormatter(format="0.00"),
                                            width=10),
                                        TableColumn(
                                            field='exptime',
                                            title='Exptime [sec]',
                                            formatter=NumberFormatter(format="0.00"),
                                            width=10),
                                        TableColumn(
                                            field='time',
                                            title='Date [UTC]',
                                            width=60,
                                            formatter=DateFormatter(format="%m/%d/%Y %H:%M")),
                                        TableColumn(
                                            field='num_images',
                                            title='Images',
                                            width=10),
                                    ])

        return Panel(title='Recent Observations',
                     child=column(self.data_table),
                     )

    def update_plot(self, dataframe=None):
        pass

    def busy(self):
        pass

    def unbusy(self):
        pass
