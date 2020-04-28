import param
import panel as pn
import hvplot.pandas  # noqa
from datetime import datetime as dt

START_DATE = dt.strptime('2018-01-01', '%Y-%M-%d')
COLLECTION = 'observations'


class ObservationsExplorer(param.Parameterized):
    """Param interface for inspecting observations"""
    df = param.DataFrame(doc='The dataframe for the observations.', precedence=-1)

    #     end_date = param.Date(default=dt.now())

    ra = param.Range(doc='RA [degrees]', default=(20, 30), bounds=(-180, 180), label='RA [deg]')
    dec = param.Range(doc='Dec [degrees]', default=(30, 40), bounds=(-90, 90), label='Dec [deg]')
    time = param.DateRange(label='Date Range',
                           default=(START_DATE, dt.now()),
                           bounds=(START_DATE, dt.now())
                           )
    min_num_images = param.Integer(doc='Minimum number of images.', default=1, bounds=(1, 50))
    field_name = param.String(doc='Field name')
    unit_id = param.ListSelector(doc='Unit IDs', label='Unit IDs')

    def __init__(self, firestore_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._firestore_db = firestore_client
        self.collection = self._firestore_db.collection(COLLECTION)
        self.get_data(*args, **kwargs)

        # Set some default for the params now that we have data.
        units = sorted(self.df.unit_id.unique().tolist())
        units.insert(0, 'The Whole World! 🌎')
        self.param.unit_id.objects = units
        self.unit_id = [units[0]]

    @param.depends('time', 'min_num_images')
    def plot(self):
        t0 = self.time[0].astimezone()
        t1 = self.time[1].astimezone()
        min_num_images = self.min_num_images

        df1 = self.df.query('time > @t0 and time < @t1 and num_images >= @min_num_images')

        columns = [
            'time',
            'unit_id',
            'sequence_id',
            'field_name',
            'ra',
            'dec',
            'exptime',
            'status',
            'total_minutes_exptime'
        ]
        df1 = df1[columns]

        return pn.widgets.DataFrame(df1.set_index(['time']),
                                    name='Recent Observations',
                                    widths=dict(
                                        unit_id=25,
                                        sequence_id=150,
                                        field_name=150,
                                        ra=10,
                                        dec=10,
                                        exptime=10,
                                        status=50,
                                        total_minutes_exptime=15
                                    ),
                                    height=400,
                                    )

    def get_data(self, query_fn=None, limit=100, *args, **kwargs):
        """Make the datasource.

        By default this will pull the most recent observations. You can pass a
        `query_fn` callable that has a `google.cloud.firestore.collection.CollectionReference`
        as the first and only parameter.  This function should return a
        `google.cloud.firestore.query.Query` instance.

        Args:
            query_fn (callable|None, optional): A callable function to get the data from the
            collection. See description for details.
            limit (int, optional): Limit the number of documents, default 100.
            *args: Description
            **kwargs: Description
        """
        # Default search for recent documents.
        self.df = get_data()

        self.df['month_name'] = self.df.time.apply(lambda t: t.month_name())
        self.df['week'] = self.df.time.apply(lambda t: t.week)
        self.df['day'] = self.df.time.apply(lambda t: t.day)

        return self
