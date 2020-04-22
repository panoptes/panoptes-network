from bokeh.models import Div
from bokeh.layouts import column

from modules.base import BaseModule

TITLE = ''


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model)

    def make_plot(self):
        self.summary = Div(text=self.get_template(), width=300, height=600)

        # Add listen event
        def select_row(attr, old, new):
            self.update_plot()

        self.model.data_source.selected.on_change('indices', select_row)

        return column(self.summary)

    def update_plot(self, dataframe=None):
        self.summary.text = self.get_template()

    def busy(self):
        pass

    def unbusy(self):
        pass

    def get_template(self):
        observation = self.model.data_frame.iloc[0]
        return f"""
        <div class="pricing-table row">
            <div class="package featured" style="text-align: left">
                <div class="package-name">
                {observation.sequence_id}
                </div>
                <ul class="features">
                    <li><strong>Time:</strong> {observation.time:%Y-%m-%d %H:%M}</li>
                    <li><strong>Unit:</strong> {observation.unit_id}</li>
                    <li><strong>Field:</strong> {observation.field_name}</li>
                    <li><strong>Coords:</strong> {observation.ra:.03f}&deg;  {observation.dec:+.03f} &deg;</li>
                    <li><strong>Exptime:</strong> {observation.exptime} seconds</li>
                    <li><strong>Camera:</strong> {observation.camera_id}</li>
                    <li><strong>ISO:</strong> {observation.iso}</li>
                    <li><strong>Status:</strong> {observation.status}</li>
                    <li><strong>Software:</strong> {observation.software_version}</li>
                </ul>
            </div>
        </div>
        """
