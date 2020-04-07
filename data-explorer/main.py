# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row, gridplot
from bokeh.models import Panel, Tabs
from bokeh.models.widgets import Div

from models.observations import Model as ObservationModel

from modules.observations.recent_table import Module as ObservationsRecentTable
from modules.observations.summary import Module as ObservationSummary
from modules.observations.summary_plot import Module as ObservationSummaryPlot
from modules.images.table import Module as ImagesTable
from modules.images.previewer import Module as ImagePreviewer


models = {
    'observations': ObservationModel().make_datasource()
}


sequence_id = 'PAN012_358d0f_20180824T035917'

module_list = [
    ObservationsRecentTable,
    ObservationSummary,
    ObservationSummaryPlot,
    ImagePreviewer,
    ImagesTable,
]

modules = {}
for module_class in module_list:
    print(f'Initializing {module_class}')
    # Pass the observations model.
    module = module_class(models['observations'])
    modules[module.id] = module

print(f'Initialized {len(modules)} modules: {modules.keys()}')

# Get all the bokeh blocks.
blocks = {module.id: getattr(module, 'make_plot')() for module in modules}


def select_observation(attr, old_index, new_index):
    new_sequence_id = models['observations'].data_source.data['sequence_id'][new_index]
    print(f'Selecting new observation: {new_sequence_id}')
    # Update modules
    for module in modules:
        try:
            getattr(module, 'update_plot')()
        except Exception as e2:
            print(f'Error updating {module.id}: {e2!r}')


# Set up an event for when the selected observation changes.
models['observations'].data_source.selected.on_change('indices', select_observation)

# heading fills available width
heading = Div(text='<h3 class="title">Data Explorer</h3>',
              height=80,
              sizing_mode="stretch_both")


observation_tab = Panel(title='Observation',
                        child=gridplot([[
                            blocks['modules.observations.summary'],
                            blocks['modules.observations.background'],
                            column(blocks['modules.images.previewer'], blocks['modules.images.table']),
                        ]]
                        ))

tabs = Tabs(tabs=[
    blocks['modules.observations.recent_table'],
    observation_tab
], sizing_mode='stretch_width')
layout = column(heading, row(tabs), sizing_mode="stretch_width")


# Lay out the current document.
curdoc().add_root(layout)
curdoc().title = "Data Explorer"
