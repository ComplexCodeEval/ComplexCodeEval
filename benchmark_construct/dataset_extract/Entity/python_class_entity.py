# python class entity

class pythonClassEntity:
    def __init__(self, node):
        self.node = node
        self.class_name = None
        self.variables = {}
        self.function_entity = []
        self.belong_file = None
        self.decorator = []
        self.is_test_class = False

    def clear_node(self):
        for function_entity in self.function_entity:
            function_entity.clear_node()
        self.node = None
    
    def clear_index(self):
        for function_entity in self.function_entity:
            function_entity.clear_index()
        self.function_entity = None

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop('node', None)
        class_dict.pop('belong_file', None)
        function_entity = [entity.to_dict() for entity in self.function_entity]
        class_dict['function_entity'] = function_entity
        return class_dict

    def set_class_name(self, class_name):
        self.class_name = class_name

    def set_variables(self, name, value):
        self.variables[name] = value

    def set_belong_file(self, belongs_file):
        self.belong_file = belongs_file

    def set_function_entity(self, function_entity):
        self.function_entity.append(function_entity)

    def set_decorator(self, decorator):
        self.decorator.append(decorator)

    def set_is_test_class(self):
        self.is_test_class = True

    def get_node(self):
        return self.node

    def get_class_name(self):
        return self.class_name

    def get_variables(self):
        return self.variables

    def get_belong_file(self):
        return self.belong_file

    def get_function_entity(self):
        return self.function_entity

    def get_decorator(self):
        return self.decorator

    def get_is_test_class(self):
        return self.is_test_class
