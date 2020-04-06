import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Segment
from bokeh.models import LinearAxis, Range1d, LegendItem
from bokeh.layouts import column
from modules.base import BaseModule

TITLE = ''


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model)
        # Make a copy
        self.background_table = self.make_background_table()
        self.airmass_table = self.make_airmass_table()
        self.line_source = None
        self.plot = None
        self.title = None

    def make_plot(self):
        self.plot = figure(title='Observation',
                           x_axis_type='datetime',
                           name="observation_background",
                           toolbar_location='above',
                           tools=self.TOOLS
                           )
        self.plot.xaxis.axis_label = 'Time [UTC]'
        self.plot.yaxis.axis_label = 'Counts [ADU]'
        self.plot.background_fill_color = "#fafafa"

        # Add listen event
        def select_row(attr, old, new):
            self.update_plot()

        self.model.data_source.selected.on_change('indices', select_row)

        self.make_background_plot()
        self.make_airmass_plot()
        self.make_vertical_line()

        return column(self.plot)

    def make_background_plot(self):
        for color in ['red', 'green', 'blue']:
            src = ColumnDataSource(self.background_table.query('color == @color'))
            self.plot.line(x='time', y='median_value', source=src, line_color=color, legend_label=f'{color[0].upper()} median background')
            self.plot.circle(x='time', y='median_value', source=src, line_color=color)

    def make_airmass_plot(self):
        # Create an airmass range.
        self.plot.extra_y_ranges['airmass'] = Range1d(5.6, 1)

        self.plot.line(x='time', y='airmass',
                       source=self.airmass_table,
                       y_range_name='airmass',
                       line_color='orange',
                       line_width=2,
                       line_alpha=0.5,
                       legend_label='Airmass'
                       )

        ax2 = LinearAxis(y_range_name="airmass", axis_label="Airmass")
        # ax2.bounds = (2, 1)
        self.plot.add_layout(ax2, 'right')

    def make_vertical_line(self):
        # Vertical line marker at selected image.
        selected_time = self.background_table.time[self.model.data_source.selected.indices[0]]
        self.line_source = ColumnDataSource(pd.DataFrame({
            'y_min': [0],
            'y_max': self.background_table.median_value.max(),
            'x_start': selected_time,
            'x_end': selected_time
        }, index=[0]))
        glyph = Segment(x0='x_start', y0='y_min',
                        x1='x_end', y1='y_max',
                        line_width=1,
                        line_alpha=0.5,
                        line_dash='dashed',
                        )
        self.plot.add_glyph(self.line_source, glyph)

    def update_plot(self, dataframe=None):
        # Update marker line.
        new_time = self.model.data_frame.time.iloc[self.model.data_source.selected.indices[0]]
        self.line_source.data.update(pd.DataFrame({
            'x_start': new_time,
            'x_end': new_time
        }, index=[0]))

        # Update RGB legend.
        for i, color in enumerate(['red', 'green', 'blue']):
            row = self.background_table.query('time == @new_time & color == @color').iloc[0]
            self.plot.legend.items[i] = LegendItem(
                label=f'BG {color[0].upper()} μ={row.median_value:7.2f} σ={row.rms:5.2f}',
                renderers=[self.plot.renderers[i * 2]],
            )

        # Update airmass legend.
        airmass = self.airmass_table.query('time == @new_time').iloc[0].airmass
        self.plot.legend.items[-1] = LegendItem(
            label=f'Airmass = {airmass:.2f}',
            renderers=[self.plot.renderers[6]],  # 3 is airmass
        )

    def busy(self):
        pass

    def unbusy(self):
        pass

    def make_background_table(self):

        # Get the time and median, melt into tidy format and then split color into separate column.
        bg_median = self.model.data_frame.filter(regex='background_median|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='median_value')
        bg_median = bg_median.join(bg_median.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Same as above for rms.
        bg_rms = self.model.data_frame.filter(regex='background_rms|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='rms')
        bg_rms = bg_rms.join(bg_rms.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Return the joined set.
        bg_df = bg_median.merge(bg_rms)
        bg_df.color = bg_df.color.map({'r': 'red', 'g': 'green', 'b': 'blue'})
        return bg_df

    def make_airmass_table(self):
        airmass_table = self.model.data_frame.filter(regex='airmass|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='airmass') \
            .drop(columns=['metric'])

        return airmass_table
