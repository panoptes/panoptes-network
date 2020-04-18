import holoviews as hv
from bokeh.io import curdoc
from bokeh.layouts import layout

# Bokeh basics

hv.extension('bokeh', 'matplotlib')
renderer = hv.renderer('bokeh').instance(mode='server')

from models.observations import Model as ObservationModel
from models.stats import Model as StatsModel

from modules.observations.table import Module as ObservationsRecentTable
from modules.stats.table import Module as StatsTable

# from modules.observations.summary import Module as ObservationSummary
# from modules.observations.summary_plot import Module as ObservationSummaryPlot
# from modules.images.table import Module as ImagesTable
# from modules.images.previewer import Module as ImagePreviewer


models = {
    'observations': ObservationModel().get_data(),
    'stats': StatsModel().get_data()
}

module_list = [
    ObservationsRecentTable(models['observations']),
    StatsTable(models['stats']),
    # ObservationSummary,
    # ObservationSummaryPlot,
    # ImagePreviewer,
    # ImagesTable,
]

print(f'Initialized {len(module_list)} modules')

doc = curdoc()

# Render all the bokeh blocks.
blocks = {
    module.id: renderer.get_plot(getattr(module, 'make_plot')(), doc)
    for module
    in module_list
}

# def select_observation(attr, old_index, new_index):
#     """ Event call back when new observation is selected. """
#     new_sequence_id = models['observations'].data_source.data['sequence_id'][new_index]
#     print(f'Selecting new observation: {new_sequence_id}')
#     # Update modules
#     for module in modules:
#         try:
#             getattr(module, 'update_plot')()
#         except Exception as e2:
#             print(f'Error updating {module.id}: {e2!r}')
#
#
# # Set up an event for when the selected observation changes.
# models['observations'].data_source.selected.on_change('indices', select_observation)


# layout = points + hv.DynamicMap(selected_info, streams=[selection])

# Combine the holoviews plot and widgets in a layout
plot = layout([
    [
        blocks['modules.observations.table'].state,
        blocks['modules.stats.table'].state,
    ]
], sizing_mode='stretch_both')

doc.add_root(plot)
doc.title = 'Modified title'
