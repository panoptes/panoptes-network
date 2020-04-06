# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import Panel, Tabs

from models import Model
import modules.images.table
import modules.images.previewer
import modules.observations.background
import modules.observations.summary
import modules.observations.recent_table

sequence_id = 'PAN008_62b062_20190924T115032'

# Fetch the initial data.
images_model = Model.get_model('images')
images_model.get_documents(sequence_id)

observation_model = Model.get_model('observations')
observation_model.get_document(sequence_id)
recent_obs_model = Model.get_model('observations')
recent_obs_model.get_recent(limit=100)

modules = [
    modules.images.table.Module(images_model),
    modules.images.previewer.Module(images_model),
    modules.observations.background.Module(images_model),
    modules.observations.summary.Module(observation_model),
    modules.observations.recent_table.Module(recent_obs_model),
]

# Get all the bokeh blocks.
blocks = {module.id: getattr(module, 'make_plot')() for module in modules}


observation_list_tab = Panel(title='Recent Observations', child=row(
    blocks['modules.observations.recent_table']
))

observation_tab = Panel(title='Observation', child=row(
    column(
        blocks['modules.observations.summary']
    ),
    column(
        blocks['modules.observations.background'],
    ),
    column(
        blocks['modules.images.previewer'],
        blocks['modules.images.table'],
    )
))

tabs = Tabs(tabs=[
    observation_list_tab,
    observation_tab
])

# Lay out the current document.
curdoc().add_root(row(tabs))
curdoc().title = "Data Explorer"
