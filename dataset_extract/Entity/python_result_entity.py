# python result entity

class pythonResultEnity:
    def __init__(self):
        self.git_group = None
        self.git_name = None
        self.version = None
        self.language = None
        self.project_name = None
        self.create_time = None
        self.update_time = None
        self.file_path = None
        self.file_name = None
        self.focal_class = None
        self.focal_name = None
        self.focal_parameter = []
        self.solution = None
        self.function_signature = None
        self.left_context = None
        self.right_context = None
        self.test_function = []
        self.import_text = []
        self.prompt = None
        self.comment = None
        self.prompt_is_gen_from_api = False

    def set_git_group(self, git_group):
        self.git_group = git_group

    def set_git_name(self, git_name):
        self.git_name = git_name

    def set_version(self, version):
        self.version = version

    def set_language(self, language):
        self.language = language

    def set_project_name(self, project_name):
        self.project_name = project_name

    def set_create_time(self, create_time):
        self.create_time = create_time

    def set_update_time(self, update_time):
        self.update_time = update_time

    def set_file_path(self, file_path):
        self.file_path = file_path

    def set_file_name(self, file_name):
        self.file_name = file_name

    def set_focal_class(self, focal_class):
        self.focal_class = focal_class

    def set_focal_name(self, focal_name):
        self.focal_name = focal_name

    def set_focal_parameter(self, focal_parameter):
        self.focal_parameter.append(focal_parameter)

    def set_solution(self, solution):
        self.solution = solution

    def set_function_signature(self, function_signature):
        self.function_signature = function_signature

    def set_left_context(self, left_context):
        self.left_context = left_context

    def set_right_context(self, right_context):
        self.right_context = right_context

    def set_test_function(self, test_function):
        self.test_function.append(test_function)

    def set_import_text(self, import_text):
        self.import_text.append(import_text)

    def set_prompt(self, prompt):
        self.prompt = prompt

    def set_is_gen_from_api(self):
        self.prompt_is_gen_from_api = True

    def set_comment(self, comment):
        self.comment = comment

    def get_git_group(self):
        return self.git_group

    def get_git_name(self):
        return self.git_name

    def get_version(self):
        return self.version

    def get_language(self):
        return self.language

    def get_project_name(self):
        return self.project_name

    def get_create_time(self):
        return self.create_time

    def get_update_time(self):
        return self.update_time

    def get_file_path(self):
        return self.file_path

    def get_file_name(self):
        return self.file_name

    def get_focal_class(self):
        return self.focal_class

    def get_focal_name(self):
        return self.focal_name

    def get_focal_parameter(self):
        return self.focal_parameter

    def get_solution(self):
        return self.solution

    def get_function_signature(self):
        return self.function_signature

    def get_left_context(self):
        return self.left_context

    def get_right_context(self):
        return self.right_context

    def get_test_function(self):
        return self.test_function

    def get_import_text(self):
        return self.import_text

    def get_prompt(self):
        return self.prompt

    def get_is_gen_from_api(self):
        return self.prompt_is_gen_from_api
    
    def get_comment(self):
        return self.comment
