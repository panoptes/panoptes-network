from modules.base import BaseModule


class Module(BaseModule):
    def __init__(self, model):
        super().__init__(model)

    def make_plot(self):
        return self.model.table

    def update_plot(self, dataframe=None):
        pass

    def busy(self):
        pass

    def unbusy(self):
        pass
