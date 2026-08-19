class ManageData:
    def __init__(self):
        self.data = []
        self.documents = []

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

    def get_documents(self):
        return self.documents

    def set_documents(self, documents):
        self.documents = documents


store = ManageData()
