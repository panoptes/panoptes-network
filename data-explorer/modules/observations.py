import os
from io import StringIO

import hvplot.pandas  # noqa
import pandas as pd  # noqa
import panel as pn
import param
import pendulum
from astropy.coordinates import SkyCoord
from astropy.utils.data import download_file
from bokeh.models import (ColumnDataSource, DataTable, TableColumn, NumberFormatter, DateFormatter)
from panoptes.utils.data import search_observations, get_metadata
from panoptes.utils.logger import logger

logger.enable('panoptes')
pn.extension()

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')
BASE_URL = os.getenv('BASE_URL', 'https://storage.googleapis.com/panoptes-exp.appspot.com/observations.csv')
OBSERVATIONS_BASE_URL = os.getenv('OBSERVATIONS_BASE_URL', 'https://storage.googleapis.com/panoptes-observations')

now = pendulum.now().replace(tzinfo=None)


class ObservationsExplorer(param.Parameterized):
    """Param interface for inspecting observations"""
    observation_df = param.DataFrame(
        doc='The DataFrame for the observations.',
        precedence=-1  # Don't show widget
    )
    images_df = param.DataFrame(
        doc='The DataFrame for the images from the selected observations.',
        precedence=-1  # Don't show widget
    )
    show_recent = param.Boolean(
        label='Show recent observations',
        doc='Show recent observations',
        default=True
    )
    search_name = param.String(
        label='Coordinates for object',
        doc='Field name for coordinate lookup',
    )
    coords = param.XYCoordinates(
        label='RA/Dec Coords [deg]',
        doc='RA/Dec Coords [degrees]',
        default=(0, 0)
    )
    radius = param.Number(
        label='Search radius [deg]',
        doc='Search radius [degrees]',
        default=15.,
        bounds=(0, 180),
        softbounds=(0, 25)
    )
    time = param.DateRange(
        label='Date Range',
        default=(pendulum.parse('2016-01-01').replace(tzinfo=None), now),
        bounds=(pendulum.parse('2016-01-01').replace(tzinfo=None), now)
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        logger.debug(f'Getting recent stats from {BASE_URL}')
        self._observations_path = download_file(f'{BASE_URL}',
                                                cache='update',
                                                show_progress=False,
                                                pkgname='panoptes')
        self._observations_df = pd.read_csv(self._observations_path).convert_dtypes()

        # Setup up widgets

        # Set some default for the params now that we have data.
        units = sorted(self._observations_df.unit_id.unique())
        units.insert(0, 'The Whole World! 🌎')
        self.param.unit_id.objects = units
        self.unit_id = [units[0]]

        # Create the source objects.
        self.update_dataset()

    @param.depends('coords', 'radius', 'time', 'min_num_images', 'unit_id', 'search_name')
    def update_dataset(self):
        if self.show_recent:
            # Get just the recent result on initial load
            df = search_observations(ra=180,
                                     dec=0,
                                     radius=180,
                                     start_date=now.subtract(months=1),
                                     end_date=now,
                                     min_num_images=1,
                                     source=self._observations_df
                                     ).sort_values(by=['time', 'unit_id', 'camera_id'], ascending=False)
        else:
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

            # Search for the observations given the current params.
            df = search_observations(ra=self.coords[0],
                                     dec=self.coords[1],
                                     radius=self.radius,
                                     start_date=self.time[0],
                                     end_date=self.time[1],
                                     min_num_images=self.min_num_images,
                                     unit_id=unit_ids
                                     ).sort_values(by=['time', 'unit_id', 'camera_id'], ascending=False)

        df.time = pd.to_datetime(df.time)
        cds = ColumnDataSource(data=df, name='observations_source')

        def obs_row_selected(attrname, old_row_index, new_row_index):
            # We only lookup one even if they select multiple rows.
            newest_index = new_row_index[-1]
            row = df.iloc[newest_index]
            print(f'Looking up sequence_id={row.sequence_id}')
            self.images_df = get_metadata(sequence_id=row.sequence_id)
            if self.images_df is not None:
                self.images_df = self.images_df.dropna()

        cds.selected.on_change('indices', obs_row_selected)

        return cds

    @param.depends("images_df")
    def selected_title(self):
        try:
            sequence_id = self.images_df.sequence_id.iloc[0]
        except AttributeError:
            sequence_id = ''
        return pn.panel(f'<h5>{sequence_id}</h5>')

    @param.depends('images_df')
    def image_table(self):
        columns = [
            ('time', 'Time [UTC]')
        ]
        try:
            images_table = self.images_df.hvplot.table(columns=columns).opts(
                width=250,
                height=100,
                title=f'Images ({len(self.images_df)})',
            )
        except AttributeError:
            images_table = self.images_df

        return images_table

    @param.depends('images_df')
    def image_preview(self):
        try:
            image_url = self.images_df.public_url.dropna().iloc[0].replace('.fits.fz', '.jpg')
            return pn.pane.HTML(f'''
                <div class="media" style="width: 300px; height: 200px">
                    <a href="{image_url}" target="_blank">
                      <img src="{image_url}" class="card-img-top" alt="Observation Image">
                    </a>
                </div>
            ''')
        except AttributeError:
            return ''

    @param.depends('observation_df')
    def fits_file_list_to_csv_cb(self):
        """ Generates a CSV file from current image list."""
        df = self.images_df.public_url.dropna()
        sio = StringIO()
        df.to_csv(sio, index=False, header=False)
        sio.seek(0)
        return sio

    def table_download_button(self):
        """ A button for downloading the images CSV."""
        try:
            sequence_id = self.images_df.sequence_id.iloc[0]
            return pn.widgets.FileDownload(
                callback=self.fits_file_list_to_csv_cb,
                filename=f'fits-list-{sequence_id}.txt',
                label='Download FITS List (.txt)',
            )
        except AttributeError:
            return ''

    def sources_download_button(self):
        try:
            sequence_id = self.images_df.sequence_id.iloc[0]
            parquet_url = f'{OBSERVATIONS_BASE_URL}/{sequence_id}-sources.parquet'
            source_btn = pn.widgets.Button(
                name='Download sources list (.parquet)',
            )

            source_btn.js_on_click(args=dict(url=parquet_url), code='''
                window.open(url, '_blank')
            ''')

            return source_btn
        except AttributeError:
            return ''

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
                width=130,
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
                field="status",
                title="Status",
                width=75,
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

        cds = self.update_dataset()
        data_table = DataTable(
            source=cds,
            name='observations_table',
            columns=columns,
            index_position=None,
            min_width=1100,
            fit_columns=True,
            sizing_mode='stretch_both',
        )

        return data_table
