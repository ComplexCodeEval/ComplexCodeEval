# python function entity


class pythonFunctionEntity:
    def __init__(self, node):
        self.node = node
        self.function_name = None
        self.parameter_entity = []
        self.variables = {}
        self.call_method = []
        self.belong_file = None
        self.belong_class = None
        self.comment = None
        self.decorator = []
        self.is_test_function = False
        self.left_context = None
        self.right_context = None
        self.function_signature = None

    def clear_node(self):
        for parameter_entity in self.parameter_entity:
            parameter_entity.clear_node()
        for call_method in self.call_method:
            call_method.clear_node()
        self.node = None

    def clear_index(self):
        for parameter_entity in self.parameter_entity:
            parameter_entity.clear_index()
        for call_method in self.call_method:
            call_method.clear_index()

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop("node", None)
        class_dict.pop("belong_file", None)
        class_dict.pop("belong_class", None)
        parameter_entity = [entity.to_dict() for entity in self.parameter_entity]
        call_method = [entity.to_dict() for entity in self.call_method]
        class_dict["parameter_entity"] = parameter_entity
        class_dict["call_method"] = call_method
        return class_dict

    def set_function_name(self, function_name):
        self.function_name = function_name

    def set_parameter_entity(self, parameter_entity):
        self.parameter_entity.append(parameter_entity)

    def set_variables(self, name, value):
        self.variables[name] = value

    def set_call_method(self, call_method):
        self.call_method.append(call_method)

    def set_belong_file(self, belong_file):
        self.belong_file = belong_file

    def set_belong_class(self, belong_class):
        self.belong_class = belong_class

    def set_comment(self, comment):
        self.comment = comment

    def set_decorator(self, decorator):
        self.decorator.append(decorator)

    def set_is_test_function(self):
        self.is_test_function = True

    def set_left_context(self, left_context):
        self.left_context = left_context

    def set_right_context(self, right_context):
        self.right_context = right_context

    def set_function_signature(self, function_signature):
        self.function_signature = function_signature

    def get_node(self):
        return self.node

    def get_function_name(self):
        return self.function_name

    def get_parameter_entity(self):
        return self.parameter_entity

    def get_variables(self):
        return self.variables

    def get_call_method(self):
        return self.call_method

    def get_belong_file(self):
        return self.belong_file

    def get_belong_class(self):
        return self.belong_class

    def get_comment(self):
        if self.comment[0] == self.comment[1]:
            return None
        file_context = self.belong_file.node
        return "\n".join(file_context[self.comment[0] : self.comment[1]])

    def get_decorator(self):
        return self.decorator

    def get_is_test_function(self):
        return self.is_test_function

    def get_code(self):
        file_context = self.belong_file.node
        return (
            "\n".join(file_context[self.left_context : self.comment[0]])
            + "\n"
            + "\n".join(file_context[self.comment[1] : self.right_context])
        )

    def get_left_context(self):
        file_context = self.belong_file.node
        return "\n".join(file_context[: self.left_context])

    def get_right_context(self):
        file_context = self.belong_file.node
        return "\n".join(file_context[self.right_context :])

    def get_function_signature(self):
        return self.function_signature
