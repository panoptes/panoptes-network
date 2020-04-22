import param


class BaseModel(param.Parameterized):
    
    collection = param.String()

    def __init__(self, collection_name, firestore_client=None):
        self.id = self.__module__

        self.collection_name = collection_name
        self.collection = firestore_client.collection(self.collection_name)

        self.query_object = None
        self.data_source = None
        self.df = None


    @param.depends()
    def table(self):
        pass

    @param.depends()
    def plot(self):
        pass