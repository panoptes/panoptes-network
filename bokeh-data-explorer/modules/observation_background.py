import pandas as pd

from bokeh.plotting import figure
from bokeh.models import Panel, ColumnDataSource, Segment
from bokeh.layouts import column


def get_tab(images_src):

    def make_dataset(orig_src):
        # Make a copy
        images = pd.DataFrame(orig_src.data)

        # Get the time and median, melt into tidy format and then split color into separate column.
        bg_median = images.filter(regex='background_median|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='median')
        bg_median = bg_median.join(bg_median.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Same as above for rms.
        bg_rms = images.filter(regex='background_rms|^time') \
            .melt(id_vars=['time'], var_name='metric', value_name='rms')
        bg_rms = bg_rms.join(bg_rms.metric.str.split('_', expand=True)) \
            .drop(columns=[0, 1, 'metric']).rename(columns={2: 'color'})

        # Retur the joined set.
        bg_df = bg_median.merge(bg_rms)
        bg_df.color = bg_df.color.map({'r': 'red', 'g': 'green', 'b': 'blue'})
        return bg_df

    def make_plot(df):
        p = figure(title='Background', x_axis_type='datetime')
        p.xaxis.axis_label = 'Time [UTC]'
        p.yaxis.axis_label = 'Counts [ADU]'
        df.time = pd.to_datetime(df.time)

        for color in ['red', 'green', 'blue']:
            src = ColumnDataSource(df.query('color == @color'))
            p.line(x='time', y='median', source=src, color=color)
            p.circle(x='time', y='median', source=src, color=color)

        # Vertical line marker at selected image.
        selected_time = df.time[images_src.selected.indices[0]]

        line_source = ColumnDataSource(pd.DataFrame({
            'y_min': [0],
            'y_max': [3000],
            'x_start': selected_time,
            'x_end': selected_time
        }))
        glyph = Segment(x0='x_start', y0='y_min', x1='x_end', y1='y_max')
        p.add_glyph(line_source, glyph)

        return p

    def update(attr, old, new):
        print('Changed')

    # Bind the url
    images_src.selected.on_change('indices', update)

    bg_df = make_dataset(images_src)
    plot = make_plot(bg_df)

    layout = column(plot)

    tab = Panel(child=layout, title='Background Plot')

    return tab
