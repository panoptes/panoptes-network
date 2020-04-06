class BaseModel:

    def __init__(self):
        self.id = self.__module__

    def fetch_data(self, state):
        raise NotImplementedError
