# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row, gridplot
from bokeh.models import Panel, Tabs
from bokeh.models.widgets import Div

from models import Model
import modules.images.table
import modules.images.previewer
import modules.observations.background
import modules.observations.summary
import modules.observations.recent_table

# Fetch the initial data.
images_model = Model.get_model('images')
observation_model = Model.get_model('observations')
recent_obs_model = Model.get_model('observations')
recent_obs_model.get_recent(limit=100)

sequence_id = 'PAN012_358d0f_20180824T035917'

images_model.get_documents(sequence_id)
observation_model.get_document(sequence_id)

modules = [
    modules.images.table.Module(images_model),
    modules.images.previewer.Module(images_model),
    modules.observations.background.Module(images_model),
    modules.observations.summary.Module(observation_model),
    modules.observations.recent_table.Module(recent_obs_model),
]

# Get all the bokeh blocks.
blocks = {module.id: getattr(module, 'make_plot')() for module in modules}


def select_observation(attr, old_index, new_index):
    new_sequence_id = recent_obs_model.data_frame.sequence_id.iloc[new_index].values[0]
    print(f'Selecting new observation: {new_sequence_id}')
    try:
        images_model.get_documents(new_sequence_id)
        observation_model.get_document(new_sequence_id, force=True)
    except Exception as e:
        print(f'Error setting observation: {e!r}')
    else:
        # Update modules
        for module in modules:
            try:
                getattr(module, 'update_plot')()
            except Exception as e2:
                print(f'Error updating {module.id}: {e2!r}')
    finally:
        observation_tab.title = f'Observation {new_sequence_id}'


recent_obs_model.data_source.selected.on_change('indices', select_observation)

# heading fills available width
heading = Div(text='<h3 class="title">Data Explorer</h3>',
              height=80,
              sizing_mode="stretch_width")


observation_tab = Panel(title='Observation',
                        child=gridplot([[
                            blocks['modules.observations.summary'],
                            blocks['modules.observations.background'],
                            blocks['modules.images.previewer'], blocks['modules.images.table'],
                        ]]
                        ))

tabs = Tabs(tabs=[
    blocks['modules.observations.recent_table'],
    observation_tab
])
layout = column(heading, row(tabs), sizing_mode="stretch_both")


# Lay out the current document.
curdoc().add_root(layout)
curdoc().title = "Data Explorer"
