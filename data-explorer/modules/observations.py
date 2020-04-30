import os
import pendulum

import pandas as pd  # noqa
import hvplot.pandas  # noqa
import param
import panel as pn
from astropy.coordinates import SkyCoord
from bokeh import events
from bokeh.models import (Button, ColumnDataSource, CustomJS, DataTable, DateFormatter,
                          NumberFormatter, RangeSlider, TableColumn, )

from panoptes.utils.data import search_observations

pn.extension()

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')


class ObservationsExplorer(param.Parameterized):
    """Param interface for inspecting observations"""
    collection = param.String(
        doc='Firestore collection',
        default='observations',
        readonly=True,
        precedence=-1  # Don't show widget
    )

    df = param.DataFrame(
        doc='The dataframe for the observations.',
        precedence=-1  # Don't show widget
    )
    search_name = param.String(
        label='Coordinates for object',
        doc='Field name for coordinate lookup',
    )
    coords = param.XYCoordinates(
        label='RA/Dec Coords [deg]',
        doc='RA/Dec Coords [degrees]', default=(0, 0)
    )
    radius = param.Number(
        label='Search radius [degrees]',
        doc='Search radius [degrees]',
        default=5.0,
        bounds=(0, None),
        softbounds=(1, 15)
    )
    time = param.DateRange(
        label='Date Range',
        default=(pendulum.parse('2018-01-01'), pendulum.now()),
        bounds=(pendulum.parse('2018-01-01'), pendulum.now())
    )
    min_num_images = param.Integer(
        doc='Minimum number of images.',
        default=1,
        bounds=(1, 50),
        softbounds=(1, 10)
    )
    unit_id = param.ListSelector(
        doc='Unit IDs',
        label='Unit IDs',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        # Lookup last two weeks of data by default
        self.df = search_observations(
            start_date=pendulum.now().subtract(weeks=2),
            ra=0, dec=0,
            radius=180
        )

        # Set some default for the params now that we have data.
        # TODO(wtgee) look up unit ids (once).
        units = [
            'The Whole World! 🌎',
            'PAN001',
            'PAN006',
            'PAN008',
            'PAN012',
            'PAN018',
        ]
        self.param.unit_id.objects = units
        self.unit_id = [units[0]]

    search_button = pn.widgets.Button(
        name='Search observations!',
        button_type='success',
    )

    @property
    def widget_box(self):
        def _search_callback(event):
            event.obj.name = 'Searching...'
            event.obj.button_type = 'warning'

            # Draw the plot again
            self.plot()

            event.obj.name = 'Search observations!'
            event.obj.button_type = 'success'

        self.search_button.on_click(_search_callback)

        def do_search(event):
            # If using the default unit_ids option, then search for all.
            unit_ids = self.unit_id
            if unit_ids == self.param.unit_id.objects[0:1]:
                unit_ids = self.param.unit_id.objects[1:]

            if self.search_name != '':
                coords = SkyCoord.from_name(self.search_name)
                self.coords = (
                    round(coords.ra.value, 3),
                    round(coords.dec.value, 3)
                )

            self.df = search_observations(ra=self.coords[0],
                                          dec=self.coords[1],
                                          radius=self.radius,
                                          start_date=self.time[0],
                                          end_date=self.time[1],
                                          min_num_images=self.min_num_images,
                                          unit_ids=unit_ids
                                          )

        self.search_button.on_click(do_search)

        return pn.WidgetBox(
            pn.Param(
                self.param,
                widgets={
                    'unit_id': pn.widgets.MultiChoice,
                    'search_name': {
                        "type": pn.widgets.TextInput,
                        "placeholder": "Lookup RA/Dec by object name"
                    },
                }
            ),
            self.search_button,
            min_width=325,
            min_height=600,
        )

    @param.depends('df')
    def table(self):
        columns = [
            'field_name',
            'unit_id',
            'sequence_id',
            'ra',
            'dec',
            'exptime',
            'status',
            'total_minutes_exptime',
            'num_images',
            'time',
        ]

        source = ColumnDataSource(self.df[columns].sort_values(by=['time'], ascending=False))

        columns = [
            TableColumn(field="unit_id", title="Unit ID", width=100),
            TableColumn(field="sequence_id", title="Sequence ID", width=600),
            TableColumn(field="field_name", title="Field Name", width=400),
            TableColumn(field="ra", title="RA", formatter=NumberFormatter(format="0.000"), width=100),
            TableColumn(field="dec", title="dec", formatter=NumberFormatter(format="0.000"), width=100),
            TableColumn(field="time", title="time", formatter=DateFormatter(format='%Y-%m-%d %H:%M')),
            TableColumn(field="num_images", title="Images", width=75),
            TableColumn(field="exptime", title="Exptime [sec]", formatter=NumberFormatter(format="0.00"), width=150),
            TableColumn(field="total_minutes_exptime", title="Total Minutes", formatter=NumberFormatter(format="0.0"),
                        width=150),
        ]

        data_table = DataTable(source=source, columns=columns, width=1000)

        def row_selected(attrname, old, new):
            row = self.df.iloc[new]
            print(row)

        source.selected.on_change('indices', row_selected)

        return data_table
