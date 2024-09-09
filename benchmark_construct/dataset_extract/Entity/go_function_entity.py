class goFunctionEntity:
    def __init__(self, node):
        self.node = node
        self.function_name = ""
        self.function_signature = ""
        self.parameters = []
        self.is_test_function = False
        self.call_methods = []
        self.variables = {}
        self.belong_class = None
        self.belong_file = None
        self.left_context = None
        self.right_context = None
        self.comment = None

    def show(self):
        print("--->Function: " + self.function_name)
        for item in self.__dict__:
            print(item, self.__dict__[item])
        for call_method in self.call_methods:
            call_method.show()
        for param_entity in self.parameters:
            param_entity.show()

    def clear_node(self):
        for param_entity in self.parameters:
            param_entity.clear_node()
        for call_method in self.call_methods:
            call_method.clear_node()
        self.node = None

    def clear_index(self):
        for param_entity in self.parameters:
            param_entity.clear_index()
        for call_method in self.call_methods:
            call_method.clear_index()

    def to_dict(self):
        class_dict = self.__dict__.copy()
        class_dict.pop("node", None)
        class_dict.pop("belong_class", None)
        class_dict.pop("belong_file", None)
        parameters = [entity.to_dict() for entity in self.parameters]
        call_methods = [entity.to_dict() for entity in self.call_methods]
        class_dict["parameters"] = parameters
        class_dict["call_methods"] = call_methods
        return class_dict

    def set_function_name(self, function_name):
        self.function_name = function_name

    def set_function_signature(self, function_signature):
        self.function_signature = function_signature

    def set_parameter_entity(self, param_entity):
        self.parameters.append(param_entity)

    def set_is_test_function(self):
        self.is_test_function = True

    def set_call_method(self, call_method):
        self.call_methods.append(call_method)

    def set_variables(self, key, value):
        self.variables[key] = value

    def set_belong_class(self, belong_class):
        self.belong_class = belong_class

    def set_belong_file(self, belong_file):
        self.belong_file = belong_file

    def get_variables(self):
        return self.variables

    def set_left_context(self, left_context):
        self.left_context = left_context

    def set_right_context(self, right_context):
        self.right_context = right_context

    def set_comment(self, comment):
        self.comment = comment

    def get_is_test_function(self):
        return self.is_test_function

    def get_belong_file(self):
        return self.belong_file

    def get_belong_class(self):
        return self.belong_class

    def get_function_name(self):
        return self.function_name

    def get_function_signature(self):
        return self.function_signature

    def get_parameter(self):
        return self.parameters

    def get_call_method(self):
        return self.call_methods

    def get_left_context(self):
        file_context = self.belong_file.node
        return "\n".join(file_context[: self.left_context])

    def get_right_context(self):
        file_context = self.belong_file.node
        return "\n".join(file_context[self.right_context :])

    def get_comment(self):
        if self.comment[0] == self.comment[1]:
            return None
        file_context = self.belong_file.node
        return "\n".join(file_context[self.comment[0] : self.comment[1]])

    def get_code(self):
        file_context = self.belong_file.node
        return "\n".join(file_context[self.left_context : self.right_context])

    def get_node(self):
        return self.node
