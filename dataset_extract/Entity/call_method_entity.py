# java call method entity

class callMethodEntity:
    def __init__(self, node):
        self.node = node
        self.call_method_name = None
        self.parameter_entity = []
        self.belong_method = None

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop('node', None)
        class_dict.pop('belong_method', None)
        parameter_entity = [entity.to_dict() for entity in self.parameter_entity]
        class_dict['parameter_entity'] = parameter_entity
        return class_dict

    def set_call_method_name(self, call_method_name):
        self.call_method_name = call_method_name

    def set_parameter_entity(self, parameter_entity):
        self.parameter_entity.append(parameter_entity)

    def set_belong_method(self, belong_method):
        self.belong_method = belong_method

    def get_node(self):
        return self.node

    def get_call_method_name(self):
        return self.call_method_name

    def get_parameter_entity(self):
        return self.parameter_entity

    def get_belong_method(self):
        return self.belong_method
