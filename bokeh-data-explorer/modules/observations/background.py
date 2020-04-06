import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Segment
from bokeh.layouts import column
from modules.base import BaseModule

TITLE = ''


class Module(BaseModule):
    def __init__(self, source):
        super().__init__(source)
        # Make a copy
        self.images_table = pd.DataFrame(self.source.data)
        self.background_table = self.make_background_table()
        self.airmass_table = self.make_airmass_table()
        self.line_source = None
        self.plot = None
        self.title = None

    def make_plot(self):
        super().make_plot()

        self.plot = figure(title='Background',
                           x_axis_type='datetime',
                           name="observation_background")
        self.plot.xaxis.axis_label = 'Time [UTC]'
        self.plot.yaxis.axis_label = 'Counts [ADU]'

        self.make_background_plot()
        self.make_vertical_line()

        return column(self.plot)

    def make_background_plot(self):
        for color in ['red', 'green', 'blue']:
            src = ColumnDataSource(self.background_table.query('color == @color'))
            self.plot.line(x='time', y='median_value', source=src, color=color)
            self.plot.circle(x='time', y='median_value', source=src, color=color)

    def make_vertical_line(self):
        # Vertical line marker at selected image.
        selected_time = self.background_table.time[self.source.selected.indices[0]]
        self.line_source = ColumnDataSource(pd.DataFrame({
            'y_min': [0],
            'y_max': self.background_table.median_value.max(),
            'x_start': selected_time,
            'x_end': selected_time
        }, index=[0]))
        glyph = Segment(x0='x_start', y0='y_min', x1='x_end', y1='y_max')
        self.plot.add_glyph(self.line_source, glyph)

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

    def make_background_table(self):

        # Get the time and median, melt into tidy format and then split color into separate column.
        bg_median = self.images_table.filter(regex='background_median|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='median_value')
        bg_median = bg_median.join(bg_median.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Same as above for rms.
        bg_rms = self.images_table.filter(regex='background_rms|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='rms')
        bg_rms = bg_rms.join(bg_rms.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Return the joined set.
        bg_df = bg_median.merge(bg_rms)
        bg_df.color = bg_df.color.map({'r': 'red', 'g': 'green', 'b': 'blue'})
        return bg_df

    def make_airmass_table(self):
        airmass_table = self.images_table.filter(regex='airmass|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='airmass') \
            .drop(columns=['metric'])

        return airmass_table
