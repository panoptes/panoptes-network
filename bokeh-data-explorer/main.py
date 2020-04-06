# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import Div

from models import Model
import modules.images.table
import modules.images.previewer
import modules.observations.background


sequence_id = 'PAN008_62b062_20190924T115032'

timer = Div()


def fetch_data(sequence_id):
    results = dict()
    for model in models:
        model.get_documents(sequence_id)
        results[model.id] = model

    return results


models = [
    Model.get_model('images')
]

results = fetch_data(sequence_id)

model_lookup = {
    'modules.images.table': 'models.images',
    'modules.images.previewer': 'models.images',
    'modules.observations.background': 'models.images'
}

modules = [
    modules.images.table.Module(results['models.images']),
    modules.images.previewer.Module(results['models.images']),
    modules.observations.background.Module(results['models.images']),
]

blocks = {}
for module in modules:
    model = model_lookup[module.id]
    block = getattr(module, 'make_plot')()
    blocks[module.id] = block


curdoc().add_root(
    row(
        column(
            blocks['modules.observations.background'],
        ),
        column(
            blocks['modules.images.previewer'],
            blocks['modules.images.table'],
            timer
        )
    )
)
curdoc().title = "Data Explorer"
