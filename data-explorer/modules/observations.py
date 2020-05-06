import os
from io import StringIO

import hvplot.pandas  # noqa
import pandas as pd  # noqa
import panel as pn
import param
import pendulum
from astropy.coordinates import SkyCoord
from bokeh.models import (ColumnDataSource, DataTable, DateFormatter,
                          NumberFormatter, TableColumn)
from panoptes.utils.data import get_metadata
from panoptes.utils.data import search_observations
from panoptes.utils.logger import logger

logger.enable('panoptes')
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
    observation_df = param.DataFrame(
        doc='The DataFrame for the observations.',
        precedence=-1  # Don't show widget
    )
    images_df = param.DataFrame(
        doc='The DataFrame for the images from the selected observations.',
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
        bounds=(0, 25),
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
    search_button = pn.widgets.Button(
        name='Search observations!',
        button_type='success',
        sizing_mode='scale_width'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

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

        def do_search(event):
            event.obj.name = 'Searching...'
            event.obj.button_type = 'warning'

            self.update_data()

            event.obj.name = 'Search observations!'
            event.obj.button_type = 'success'

        self.search_button.on_click(do_search)

        # Get recent results
        self.observation_df = search_observations(ra=180,
                                                  dec=0,
                                                  radius=180,
                                                  start_date=pendulum.now().subtract(weeks=2),
                                                  end_date=pendulum.now(),
                                                  min_num_images=1,
                                                  )
        self.observation_df.sort_values(by='time', ascending=False, inplace=True)

        # Get the first image of the first observation.
        sequence_id = str(self.observation_df.iloc[0].sequence_id)
        self.images_df = get_metadata(sequence_id=sequence_id).dropna()

        # Create the source objects.
        self.observation_source = ColumnDataSource(data=self.observation_df, name='observations_source')

        def obs_row_selected(attrname, old, new):
            newest = new[-1]
            row = self.observation_df.iloc[newest]
            self.images_df = get_metadata(sequence_id=row.sequence_id).dropna()

        self.observation_source.selected.on_change('indices', obs_row_selected)

    def update_data(self):
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

        self.observation_df = search_observations(ra=self.coords[0],
                                                  dec=self.coords[1],
                                                  radius=self.radius,
                                                  start_date=self.time[0],
                                                  end_date=self.time[1],
                                                  min_num_images=self.min_num_images,
                                                  unit_ids=unit_ids
                                                  )
        self.observation_source.data = self.observation_df

    def widget_box(self):
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
            sizing_mode='stretch_both',
            max_width=320
        )

    def selected_title(self):
        sequence_id = self.images_df.sequence_id.iloc[0]
        return pn.panel(f'<h5>{sequence_id}</h5>')

    @param.depends('images_df')
    def image_table(self):
        columns = [
            ('time', 'Time [UTC]')
        ]
        images_table = self.images_df.hvplot.table(columns=columns).opts(
            width=250,
            height=200,
            title=f'Images ({len(self.images_df)})',
        )

        return images_table

    @param.depends('images_df')
    def image_preview(self):
        image_url = self.images_df.public_url.dropna().iloc[0].replace('.fits.fz', '.jpg')
        return pn.pane.HTML(f'''
            <div class="media" style="width: 300px; height: 200px">
                <a href="{image_url}" target="_blank">
                  <img src="{image_url}" class="card-img-top" alt="Observation Image">
                </a>
            </div>
        ''')

    @param.depends('observation_df')
    def fits_file_list_to_csv_cb(self):
        df = self.images_df.public_url.dropna()
        sio = StringIO()
        df.to_csv(sio, index=False, header=False)
        sio.seek(0)
        return sio

    def table_download_button(self):
        sequence_id = self.images_df.sequence_id.iloc[0]
        return pn.widgets.FileDownload(
            callback=self.fits_file_list_to_csv_cb,
            filename=f'fits-list-{sequence_id}.txt',
            label='Download FITS List (.txt)',
        )

    def sources_download_button(self):
        sequence_id = self.images_df.sequence_id.iloc[0]
        parquet_url = f'https://storage.googleapis.com/panoptes-processed-observations/{sequence_id}.parquet'
        return pn.pane.HTML(f"""
            <a href="{parquet_url}" target="_blank">Download sources list (.parquet)</a>
        """)

    @param.depends('observation_df')
    def table(self):
        columns = [
            TableColumn(
                field="unit_id",
                title="Unit ID",
                width=60,
            ),
            TableColumn(
                field="camera_id",
                title="Camera ID",
                width=60,
            ),
            TableColumn(
                field="time",
                title="Time [UTC]",
                formatter=DateFormatter(format='%Y-%m-%d %H:%M'),
                width=160,
            ),
            TableColumn(
                field="field_name",
                title="Field Name",
                width=240,
            ),
            TableColumn(
                field="ra",
                title="RA [deg]",
                formatter=NumberFormatter(format="0.000"),
                width=70,
            ),
            TableColumn(
                field="dec",
                title="Dec [deg]",
                formatter=NumberFormatter(format="0.000"),
                width=70,
            ),
            TableColumn(
                field="num_images",
                title="Images",
                width=40,
            ),
            TableColumn(
                field="exptime",
                title="Exptime [sec]",
                formatter=NumberFormatter(format="0.00"),
                width=60,
            ),
            TableColumn(
                field="total_minutes_exptime",
                title="Total Minutes",
                formatter=NumberFormatter(format="0.0"),
                width=60,
            ),
        ]

        data_table = DataTable(
            source=self.observation_source,
            name='observations_table',
            columns=columns,
            index_position=None,
            min_width=1100,
            fit_columns=True,
            sizing_mode='stretch_both',
        )

        return data_table
