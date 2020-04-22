import os
from google.cloud import firestore

import holoviews as hv
from bokeh.io import curdoc
import panel as pn

import pandas as pd  # noqa
import hvplot.pandas  # noqa

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'panoptes-exp')
FIRESTORE_DB = firestore.Client(project=PROJECT_ID)

from models.observations import ObservationsExplorer
from models.stats import Stats

models = dict(
    observations=ObservationsExplorer(firestore_client=FIRESTORE_DB),
    stats=Stats(firestore_client=FIRESTORE_DB)
)

print(f'Initialized {len(models)} models')

doc = curdoc()

plots = {
    model_name: getattr(model, 'plot')()
    for model_name, model
    in models.items()
}

observations = models['observations']
stats = models['stats']

obs_tab = pn.Row(
    pn.Row(
        pn.Tabs(
            ('Recent Observations', pn.pane.Markdown('## Recent Observations')),
            ('Search', pn.WidgetBox(
                pn.Param(
                    observations.param,
                    widgets={
                        'unit_id': pn.widgets.MultiChoice
                    }
                ),
                min_width=325,
                min_height=600,

            )),
        ),
        observations.plot,
        min_width=800,
    ),
)

stats_tab = pn.Column(
    stats.plot,
    pn.WidgetBox(
        pn.Param(
            stats.param,
            widgets={
                'year': dict(
                    type=pn.widgets.IntSlider,
                    start=int(stats.df.year.min()),
                    end=int(stats.df.year.max()),
                ),
                'metric': dict(
                    type=pn.widgets.RadioBoxGroup,
                )
            },
        ),
    )
)

layout = pn.Column(
    pn.Row(
        pn.pane.Markdown('# PANOPTES Data Explorer', sizing_mode='stretch_width'),
    ),
    pn.Tabs(
        ('Observations', obs_tab),
        ('Stats', stats_tab),
    ),
    sizing_mode='stretch_width'
).get_root()

doc.add_root(layout)
doc.title = 'PANOPTES Data Explorer'
