# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row

from models import Model
import modules.images.table
import modules.images.previewer
import modules.observations.background

sequence_id = 'PAN008_62b062_20190924T115032'

# Fetch the initial data.
images_model = Model.get_model('images')
images_model.get_documents(sequence_id)

modules = [
    modules.images.table.Module(images_model),
    modules.images.previewer.Module(images_model),
    modules.observations.background.Module(images_model),
]

# Get all the bokeh blocks.
blocks = {module.id: getattr(module, 'make_plot')() for module in modules}

# Lay out the current document.
curdoc().add_root(
    row(
        column(
            blocks['modules.observations.background'],
        ),
        column(
            blocks['modules.images.previewer'],
            blocks['modules.images.table'],
        )
    )
)
curdoc().title = "Data Explorer"
