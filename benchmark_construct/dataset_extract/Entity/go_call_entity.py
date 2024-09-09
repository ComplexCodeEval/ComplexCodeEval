class goCallEntity:
    def __init__(self, node):
        self.node = node
        self.call_api = ""
        self.belong_function = None
        self.parameters = None

    def show(self):
        print("--->Call: " + self.call_api)
        for item in self.__dict__:
            print(item, self.__dict__[item])

    def clear_node(self):
        self.node = None

    def clear_index(self):
        self.belong_function = None

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop("node", None)
        class_dict.pop("belong_function", None)
        return class_dict

    def set_call_api(self, call_api):
        self.call_api = call_api

    def set_belong_function(self, belong_function):
        self.belong_function = belong_function

    def set_parameter(self, parameter):
        self.parameters = parameter

    def get_node(self):
        return self.node

    def get_call_api(self):
        return self.call_api

    def get_belong_function(self):
        return self.belong_function

    def get_parameter(self):
        return self.parameters
