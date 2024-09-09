# java method entity


class methodEntity:
    def __init__(self, node):
        self.node = node
        self.method_name = None
        self.comment = None
        self.annotation = []
        self.parameter_entity = []
        self.variable_entity = []
        self.call_method = []
        self.belong_class = None
        self.is_test_method = False
        self.right_context = None
        self.left_context = None
        self.method_signature = None

    def clear_node(self):
        for parameter_entity in self.parameter_entity:
            parameter_entity.clear_node()
        for variable_entity in self.variable_entity:
            variable_entity.clear_node()
        for call_method in self.call_method:
            call_method.clear_node()
        self.node = None

    def clear_index(self):
        for parameter_entity in self.parameter_entity:
            parameter_entity.clear_index()
        for variable_entity in self.variable_entity:
            variable_entity.clear_index()
        for call_method in self.call_method:
            call_method.clear_index()

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop("node", None)
        class_dict.pop("belong_class", None)
        parameter_entity = [entity.to_dict() for entity in self.parameter_entity]
        variable_entity = [entity.to_dict() for entity in self.variable_entity]
        call_method = [entity.to_dict() for entity in self.call_method]
        class_dict["parameter_entity"] = parameter_entity
        class_dict["variable_entity"] = variable_entity
        class_dict["call_method"] = call_method
        return class_dict

    def set_method_name(self, method_name):
        self.method_name = method_name

    def set_comment(self, comment):
        self.comment = comment

    def set_annotation(self, annotation):
        self.annotation.append(annotation)

    def set_parameter_entity(self, parameter_entity):
        self.parameter_entity.append(parameter_entity)

    def set_variable_entity(self, variable_entity):
        self.variable_entity.append(variable_entity)

    def set_call_method(self, call_method):
        self.call_method.append(call_method)

    def set_belong_class(self, belong_class):
        self.belong_class = belong_class

    def set_is_test_method(self):
        self.is_test_method = True

    def set_right_context(self, right_context):
        self.right_context = right_context

    def set_left_context(self, left_context):
        self.left_context = left_context

    def set_method_signature(self, method_signature):
        self.method_signature = method_signature

    def get_node(self):
        return self.node

    def get_method_name(self):
        return self.method_name

    def get_comment(self):
        if self.comment is None:
            return None
        file_context = self.belong_class.belong_file.node
        return "\n".join(file_context[self.comment[0] : self.comment[1]])

    def get_annotation(self):
        return self.annotation

    def get_parameter_entity(self):
        return self.parameter_entity

    def get_variable_entity(self):
        return self.variable_entity

    def get_call_method(self):
        return self.call_method

    def get_belong_class(self):
        return self.belong_class

    def get_is_test_method(self):
        return self.is_test_method

    def get_code(self):
        file_context = self.belong_class.belong_file.node
        return "\n".join(file_context[self.left_context : self.right_context])

    def get_right_context(self):
        file_context = self.belong_class.belong_file.node
        return "\n".join(file_context[self.right_context :])

    def get_left_context(self):
        file_context = self.belong_class.belong_file.node
        return "\n".join(file_context[: self.left_context])

    def get_method_signature(self):
        return self.method_signature
