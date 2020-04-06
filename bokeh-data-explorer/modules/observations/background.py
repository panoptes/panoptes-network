import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Segment
from bokeh.layouts import column
from modules.base import BaseModule

TITLE = ''


class Module(BaseModule):
    def __init__(self, source):
        super().__init__(source)
        self.data_table = self.make_datatable()
        self.line_source = None
        self.plot = None
        self.title = None

    def make_plot(self):
        p = figure(title='Background', x_axis_type='datetime', name="observation_background")
        p.xaxis.axis_label = 'Time [UTC]'
        p.yaxis.axis_label = 'Counts [ADU]'

        for color in ['red', 'green', 'blue']:
            src = ColumnDataSource(self.data_table.query('color == @color'))
            p.line(x='time', y='median_value', source=src, color=color)
            p.circle(x='time', y='median_value', source=src, color=color)

        # Vertical line marker at selected image.
        selected_time = self.data_table.time[self.source.selected.indices[0]]

        self.plot = p

        def select_row(attr, old, new):
            self.update_plot()

        self.source.selected.on_change('indices', select_row)

        self.line_source = ColumnDataSource(pd.DataFrame({
            'y_min': [0],
            'y_max': self.data_table.median_value.max(),
            'x_start': selected_time,
            'x_end': selected_time
        }, index=[0]))
        glyph = Segment(x0='x_start', y0='y_min', x1='x_end', y1='y_max')
        p.add_glyph(self.line_source, glyph)

        return column(self.plot)

    def update_plot(self, dataframe=None):
        # Update marker line.
        new_time = self.source.data['time'][self.source.selected.indices[0]]
        self.line_source.data.update(pd.DataFrame({
            'x_start': new_time,
            'x_end': new_time
        }, index=[0]))

    def busy(self):
        self.title.text = 'Updating...'

    def unbusy(self):
        try:
            selected_index = self.source.selected.indices[0]
        except IndexError:
            print(f'No index')
            selected_index = 0

        self.title.text = self.source.data['image_id'][selected_index]

    def make_datatable(self):
        # Make a copy
        images = pd.DataFrame(self.source.data)

        # Get the time and median, melt into tidy format and then split color into separate column.
        bg_median = images.filter(regex='background_median|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='median_value')
        bg_median = bg_median.join(bg_median.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Same as above for rms.
        bg_rms = images.filter(regex='background_rms|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='rms')
        bg_rms = bg_rms.join(bg_rms.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Return the joined set.
        bg_df = bg_median.merge(bg_rms)
        bg_df.color = bg_df.color.map({'r': 'red', 'g': 'green', 'b': 'blue'})
        return bg_df
