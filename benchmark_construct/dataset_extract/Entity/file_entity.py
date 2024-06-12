# file entity

class fileEntity:
    def __init__(self, node):
        self.node = node
        self.file_name = None
        self.file_path = None
        self.package_text = None
        self.import_text = []
        self.class_entity = []
        self.function_entity = []
        self.variables = {}
        self.is_test_file = False
        self.module_name = None

    def clear_node(self):
        for class_entity in self.class_entity:
            class_entity.clear_node()
        for function_entity in self.function_entity:
            function_entity.clear_node()
        temp = self.node
        self.node = self.node.text.decode('utf-8').split('\n')
        if temp.start_point[0] == 1:
            self.node.insert(0, '') 

    def clear_index(self):
        for class_entity in self.class_entity:
            class_entity.clear_index()
        for function_entity in self.function_entity:
            function_entity.clear_index()
        self.variables = None
        self.class_entity = None
        self.function_entity = None

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop('node', None)
        class_entity = [entity.to_dict() for entity in self.class_entity]
        function_entity = [entity.to_dict() for entity in self.function_entity]
        class_dict['class_entity'] = class_entity
        class_dict['function_entity'] = function_entity
        return class_dict

    def set_file_name(self, file_name):
        self.file_name = file_name

    def set_file_path(self, file_path):
        self.file_path = file_path

    def set_package_text(self, package_text):
        self.package_text = package_text

    def set_import_text(self, import_text):
        self.import_text.append(import_text)

    def set_class_entity(self, class_entity):
        self.class_entity.append(class_entity)

    def set_is_test_file(self):
        self.is_test_file = True

    def set_module_name(self, module_name):
        self.module_name = module_name

    def set_function_entity(self, file_entity):
        self.function_entity.append(file_entity)

    def set_variables(self, name, value):
        self.variables[name] = value

    def get_node(self):
        return self.node

    def get_file_name(self):
        return self.file_name

    def get_file_path(self):
        return self.file_path

    def get_package_text(self):
        return self.package_text

    def get_import_text(self):
        return self.import_text

    def get_class_entity(self):
        return self.class_entity

    def get_is_test_file(self):
        return self.is_test_file

    def get_module_name(self):
        return self.module_name

    def get_function_entity(self):
        return self.function_entity

    def get_variables(self):
        return self.variables