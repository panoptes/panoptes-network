# Pandas for data management
import concurrent.futures
import time

# Bokeh basics
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import Div, TextInput
from bokeh.models import ColumnDataSource

from models import images as images_model
import modules.images.table
import modules.images.previewer
# import modules.background


sequence_id = 'PAN008_62b062_20190924T115032'

timer = Div()


def fetch_data(sequence_id):
    t0 = time.time()
    # Collect fetch methods for all dashboard modules
    fetch_methods = {model.id: getattr(model, 'fetch_data') for model in models}
    # Create a thread pool: one separate thread for each dashboard module
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(fetch_methods)) as executor:
        # Prepare the thread tasks
        tasks = {}
        for key, fetch_method in fetch_methods.items():
            task = executor.submit(fetch_method, sequence_id)
            tasks[task] = key
        # Run the tasks and collect results as they arrive
        results = {}
        for task in concurrent.futures.as_completed(tasks):
            key = tasks[task]
            results[key] = ColumnDataSource(task.result())
    # Return results once all tasks have been completed
    t1 = time.time()
    timer.text = f'(Execution time: {round(t1 - t0, 4)} seconds)'
    return results


def update(attrname, old, new):
    timer.text = f'(Executing {len(models)} queries...)'
    for module in modules:
        getattr(module, 'busy')()

    try:
        results = fetch_data(new)
    except Exception as e:
        print(f'Error getting sequence_id={new}: {e!r}')
        timer.text = f'Invalid Sequence ID'
    else:
        for module in modules:
            model = model_lookup[module.id]
            getattr(module, 'update_plot')(results[model].data)

        for module in modules:
            getattr(module, 'unbusy')()


models = [
    images_model.Model()
]

results = fetch_data(sequence_id)

model_lookup = {
    'modules.images.table': 'models.images',
    'modules.images.previewer': 'models.images'
}

modules = [
    modules.images.table.Module(results['models.images']),
    modules.images.previewer.Module(results['models.images']),
    # modules.background.Module()
]


sequence_id_input = TextInput(value=sequence_id, title="Sequence ID:")
sequence_id_input.on_change("value", update)

blocks = {}
for module in modules:
    model = model_lookup[module.id]
    block = getattr(module, 'make_plot')()
    blocks[module.id] = block

curdoc().add_root(
    column(
        row(column(
            blocks['modules.images.previewer'],
            blocks['modules.images.table'],
            timer
        )),
    )
)
curdoc().title = "Data Explorer"
