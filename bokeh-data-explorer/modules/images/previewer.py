from bokeh.models.widgets import Paragraph
from bokeh.layouts import column
from bokeh.models.widgets import Div
from modules.base import BaseModule

TITLE = ''

IMG_TAG = """
<a href="{0}" target="_blank">
  <img src="{0}" alt="Loading..." width=324, height=216>
</a>
"""


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model)
        self.title = Paragraph()

        self.model.data_source.selected.indices = [0]
        bucket_path = self.model.data_frame.bucket_path.iloc[0]
        image_url = bucket_path.replace('processed', 'raw').replace('.fits.fz', '.jpg')
        self.image = Div(text=IMG_TAG.format(image_url))

    def make_plot(self):
        # Add listen event
        def select_row(attr, old, new):
            self.update_plot()

        self.model.data_source.selected.on_change('indices', select_row)

        return column(self.title, self.image)

    def update_plot(self, dataframe=None):
        try:
            selected_index = self.model.data_source.selected.indices[0]
        except IndexError:
            print(f'No index')
            selected_index = 0

        self.title.text = self.model.data_frame.image_id.iloc[selected_index]

        bucket_path = self.model.data_frame.bucket_path.iloc[selected_index]
        new_url = bucket_path.replace('processed', 'raw').replace('.fits.fz', '.jpg')
        self.image.text = IMG_TAG.format(new_url)

    def busy(self):
        self.title.text = 'Updating...'

    def unbusy(self):
        pass
