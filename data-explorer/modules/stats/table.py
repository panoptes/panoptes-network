from modules.base import BaseModule

import holoviews as hv

class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model, name=__name__)

    def make_plot(self):
        return self.model.table.to(hv.Scatter, vdims=['total_hours_exptime'])

    def update_plot(self, dataframe=None):
        pass

    def busy(self):
        pass

    def unbusy(self):
        pass
