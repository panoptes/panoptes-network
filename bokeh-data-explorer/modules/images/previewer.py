from bokeh.models.widgets import Paragraph
from bokeh.layouts import column
from bokeh.models.widgets import Div
from modules.base import BaseModule

TITLE = ''

IMG_TAG = """
<a href="{}" target="_blank">
    <img src="{}" alt="Loading..." width={} height={} style="border: 1px solid black">
</a>
"""


class Module(BaseModule):
    thumb_width = 480
    thumb_height = 300

    def __init__(self, source):
        super().__init__(source)
        self.image = None
        self.title = None

    def make_plot(self):
        self.title = Paragraph()

        self.source.selected.indices = [0]
        image_url = self.source.data['image_path'][0]

        self.image = Div(text=IMG_TAG.format(image_url, image_url, self.thumb_width, self.thumb_height))

        def select_row(attr, old, new):
            self.unbusy()

        # Bind the url
        self.source.selected.on_change('indices', select_row)

        self.unbusy()
        return column(self.image)

    def update_plot(self, dataframe):
        self.source.data.update(dataframe)
        self.set_title()

    def busy(self):
        self.title.text = 'Updating...'

    def unbusy(self):
        try:
            selected_index = self.source.selected.indices[0]
        except IndexError:
            print(f'No index')
            selected_index = 0

        self.title.text = self.source.data['image_id'][selected_index]

        new_url = self.source.data['image_path'][selected_index]
        self.image.text = IMG_TAG.format(new_url, new_url, self.thumb_width, self.thumb_height)
