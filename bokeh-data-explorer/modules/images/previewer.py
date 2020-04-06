from bokeh.models.widgets import Paragraph
from bokeh.layouts import column
from bokeh.models.widgets import Div
from modules.base import BaseModule

TITLE = ''

IMG_TAG = """
<a href="{0}" target="_blank">
  <img src="{0}" alt="Loading..." width=320 height=160>
</a>
"""


class Module(BaseModule):
    def __init__(self, source):
        super().__init__(source)
        self.title = Paragraph()

        self.source.selected.indices = [0]
        image_url = self.source.data['image_path'][0]
        self.image = Div(text=IMG_TAG.format(image_url))

    def make_plot(self):
        def select_row(attr, old, new):
            self.update_plot()

        self.source.selected.on_change('indices', select_row)

        return column(self.title, self.image)

    def update_plot(self, dataframe=None):
        try:
            selected_index = self.source.selected.indices[0]
        except IndexError:
            print(f'No index')
            selected_index = 0

        self.title.text = self.source.data['image_id'][selected_index]

        new_url = self.source.data['image_path'][selected_index]
        self.image.text = IMG_TAG.format(new_url)

    def busy(self):
        self.title.text = 'Updating...'

    def unbusy(self):
        pass
