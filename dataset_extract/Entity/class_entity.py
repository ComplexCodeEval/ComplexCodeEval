#java class entity

class classEntity:
    def __init__(self, node):
        self.node = node
        self.class_name = None
        self.inheritances_name = []
        self.method_entity = []
        self.class_entity = []
        self.variable_entity = []
        self.belong_file = None
        self.comment = None

    def clear_node(self):
        for method_entity in self.method_entity:
            method_entity.clear_node()
        for class_entity in self.class_entity:
            class_entity.clear_node()
        for variable_entity in self.variable_entity:
            variable_entity.clear_node()
        self.node = None

    def clear_index(self):
        for method_entity in self.method_entity:
            method_entity.clear_index()
        for class_entity in self.class_entity:
            class_entity.clear_index()
        for variable_entity in self.variable_entity:
            variable_entity.clear_index()
        self.method_entity = None
        self.class_entity = None
        self.variable_entity = None

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop('node', None)
        class_dict.pop("belong_file", None)
        method_entity = [entity.to_dict() for entity in self.method_entity]
        class_entity = [entity.to_dict() for entity in self.class_entity]
        variable_entity = [entity.to_dict() for entity in self.variable_entity]
        class_dict['method_entity'] = method_entity
        class_dict['class_entity'] = class_entity
        class_dict['variable_entity'] = variable_entity
        return class_dict

    def set_class_name(self, class_name):
        self.class_name = class_name

    def set_inheritances_name(self, inheritances_name):
        self.inheritances_name.append(inheritances_name)

    def set_method_entity(self, method_entity):
        self.method_entity.append(method_entity)

    def set_class_entity(self, class_entity):
        self.class_entity.append(class_entity)

    def set_variable_entity(self, variable_entity):
        self.variable_entity.append(variable_entity)

    def set_belong_file(self, belong_file):
        self.belong_file = belong_file

    def set_comment(self, comment):
        self.comment = comment

    def get_node(self):
        return self.node

    def get_class_name(self):
        return self.class_name

    def get_inheritances_name(self):
        return self.inheritances_name

    def get_method_entity(self):
        return self.method_entity

    def get_class_entity(self):
        return self.class_entity

    def get_variable_entity(self):
        return self.variable_entity

    def get_belong_file(self):
        return self.belong_file

    def get_comment(self):
        return self.comment