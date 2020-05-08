#!/usr/bin/env python

import panel as pn
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore
from jinja2 import Environment, FileSystemLoader
from modules.observations import ObservationsExplorer
from modules.stats import Stats

pn.extension()

# Load the templates
env = Environment(loader=FileSystemLoader('./templates'))
main_template = env.get_template('main.html')

# TODO Override the notebook template so it renders well.
tmpl = pn.Template(main_template)

# Load the modules we want.
obs_explorer = ObservationsExplorer(name='Search Observations')
stats = Stats(name='Overall Stats',
              firestore_client=firestore.Client(project='panoptes-exp',
                                                credentials=AnonymousCredentials()))

# Create the layout we want for the obsExplorer
tmpl.add_panel('obsExplorer',
               pn.Row(
                   obs_explorer.widget_box,
                   obs_explorer.table,
                   pn.Column(
                       obs_explorer.selected_title,
                       obs_explorer.image_preview,
                       obs_explorer.table_download_button,
                       obs_explorer.sources_download_button
                   ),
                   sizing_mode='stretch_both',
               ),
               )

tmpl.add_panel('statsExplorer',
               pn.Row(
                   stats.widget_box,
                   stats.plot,
                   sizing_mode='stretch_both',
               ))

tmpl.add_variable('total_hours', int(stats.df['Total Hours'].sum()))
tmpl.add_variable('total_images', int(stats.df['Images'].sum()))
tmpl.add_variable('total_observations', int(stats.df['Observations'].sum()))
tmpl.add_variable('total_units', len(stats.df['Unit'].unique()))

tmpl.servable(title='PANOPTES Data Explorer')
