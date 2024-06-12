# parameter entity

class parameterEntity:
    def __init__(self, node):
        self.node = node
        self.parameter_name = None
        self.parameter_type = None

    def clear_node(self):
        self.node = None

    def clear_index(self):
        pass

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop('node', None)
        return class_dict

    def set_parameter_name(self, parameter_name):
        self.parameter_name = parameter_name

    def set_parameter_type(self, parameter_type):
        self.parameter_type = parameter_type

    def get_node(self):
        return self.node

    def get_parameter_name(self):
        return self.parameter_name

    def get_parameter_type(self):
        return self.parameter_type