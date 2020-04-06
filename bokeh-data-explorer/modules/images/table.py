from bokeh.models.widgets import DataTable
from bokeh.models.widgets import TableColumn
from bokeh.models.widgets import NumberFormatter
from bokeh.models.widgets import Paragraph
from bokeh.models.widgets import DateFormatter
from bokeh.layouts import column
from modules.base import BaseModule

TITLE = 'Total images: '


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model)
        self.title = Paragraph()

    def make_plot(self):
        self.set_title()

        column_width = 324  # pixels

        self.data_table = DataTable(source=self.model.data_source,
                                    width=column_width,
                                    index_position=None,
                                    columns=[
                                        TableColumn(field='time', title='Time [UTC]', width=60, formatter=DateFormatter(format="%m/%d/%Y %H:%M")),
                                        TableColumn(field='ha_mnt', title='HA [deg]', width=20, formatter=NumberFormatter(format="0.00")),
                                        TableColumn(field='airmass', title='Airmass', width=5, formatter=NumberFormatter(format="0.00")),
                                    ]
                                    )

        def select_row(attr, old, new):
            self.set_title()

        self.model.data_source.selected.on_change('indices', select_row)

        return column(
            self.title,
            self.data_table
        )

    # def update_plot(self):
    #     if dataframe is not None:
    #         self.model.data_source.data.update(dataframe)
    #     self.set_title()

    def busy(self):
        self.set_title('Updating...')

    def unbusy(self):
        self.set_title()

    def set_title(self, text=None):
        if text is None:
            text = f'{TITLE} {len(self.model.data_frame)}'

        self.title.text = text
