# 将文件解析成语法树的相关工具

from collections import Counter

from tree_sitter import Language, Parser
from dataset_extract.Entity.file_entity import fileEntity
from dataset_extract.Entity.class_entity import classEntity
from dataset_extract.Entity.method_entity import methodEntity
from dataset_extract.Entity.call_method_entity import callMethodEntity
from dataset_extract.Entity.parameter_entity import parameterEntity
from dataset_extract.Entity.python_function_entity import pythonFunctionEntity
from dataset_extract.Entity.python_class_entity import pythonClassEntity
from dataset_extract.Entity.python_call_entity import pythonCallEntity

parsers = {}

for lang in ['python', 'java']:
    LANGUAGE = Language('./dataset_extract/parser/my-languages.so', lang)
    parser = Parser()
    parser.set_language(LANGUAGE)
    parsers[lang] = parser


# 解析java文件中的api调用
def analyze_java_class(node):
    if node.type == "class_declaration":
        if class_body := node.child_by_field_name("body"):
            yield class_body
            for child in class_body.children:
                yield from analyze_java_class(child)


def analyze_java_method_api(node, method, import_packages, api_count, apis):
    if node is None:
        return
    for child in node.children:
        if child.type == "method_invocation":
            invocation_name = child.text.decode("utf-8").split('(')[0].split('.')
            if invocation_name[0] in import_packages.keys():
                if len(invocation_name) > 1:
                    api_name = import_packages[invocation_name[0]] + "." + ".".join(invocation_name[1:])
                else:
                    api_name = import_packages[invocation_name[0]]
                for api in apis:
                    flag = True
                    for accept in api["accept"]:
                        if accept not in api_name.lower():
                            flag = False
                            break
                    if not flag:
                        continue
                    for reject in api["reject"]:
                        if reject in api_name.lower():
                            flag = False
                            break
                    if not flag:
                        continue
                    api_count[api["name"]][api_name] += 1
        analyze_java_method_api(child, method, import_packages, api_count, apis)


def analyze_java_api(path, apis):
    try:
        with open(path, 'r') as file:
            api_count = {}
            for api in apis:
                api_count[api['name']] = Counter()
            import_packages = {}
            code = file.read()
            tree = parsers['java'].parse(bytes(code, 'utf8'))
            root = tree.root_node
            for child in root.children:
                if child.type == "import_declaration":
                    for import_package in child.children:
                        if import_package.type == "scoped_identifier":
                            import_package_name = import_package.text.decode("utf-8")
                            import_class_name = import_package_name.split('.')[-1]
                            import_packages[import_class_name] = import_package_name
                if child.type == "class_declaration":
                    for class_body in analyze_java_class(child):
                        for node in class_body.children:
                            if node.type == "method_declaration":
                                method_name = node.child_by_field_name("name").text.decode("utf-8")
                                analyze_java_method_api(node, method_name, import_packages, api_count, apis)
            return api_count

    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {path}, skip this file")
    except RecursionError:
        print(f"RecursionError: {path}, skip this file")


def get_annotation(node):
    if node is None:
        return
    for child in node.children:
        if child.type == "annotation":
            yield child.text.decode("utf-8")
        yield from get_annotation(child)


def get_parameter_type(parameter_type, parameter_entity):
    if "@" in parameter_type:
        for annotation in get_annotation(parameter_entity.get_node()):
            parameter_type.replace(annotation, "")
    if "<" in parameter_type:
        return get_parameter_type("".join(parameter_type.split("<")[0]), parameter_entity)
    if "." in parameter_type:
        return get_parameter_type("".join(parameter_type.split(".")[-1]), parameter_entity)
    else:
        return parameter_type


def parse_java_invoke_method(node, method_entity):
    if node is None:
        return
    for child in node.children:
        if child.type == "method_invocation":
            call_method_entity = callMethodEntity(child)
            method_entity.set_call_method(call_method_entity)
            call_method_entity.set_belong_method(method_entity)
            call_method_name = child.text.decode("utf-8").split('(')[0]
            call_method_entity.set_call_method_name(call_method_name)
            for call_method_child in child.children:
                if call_method_child.type == "argument_list":
                    for argument_child in call_method_child.children:
                        if argument_child.type != "(" and argument_child.type != ")" and argument_child.type != ",":
                            parameter_entity = parameterEntity(argument_child)
                            parameter_entity.set_parameter_type(argument_child.type)
                            parameter_entity.set_parameter_name(argument_child.text.decode("utf-8"))
                            call_method_entity.set_parameter_entity(parameter_entity)
        parse_java_invoke_method(child, method_entity)


def parse_java_method(method_entity, class_entity):
    try:
        method_node = method_entity.get_node()
        method_entity.set_belong_class(class_entity)
        method_name = method_node.child_by_field_name("name").text.decode("utf-8")
        method_entity.set_method_name(method_name)
        if method_node.prev_sibling and method_node.prev_sibling.type == "comment":
            comment = method_node.prev_sibling.text.decode("utf-8")
            method_entity.set_comment(comment)
        method_parameters = method_node.child_by_field_name("parameters")
        if method_parameters:
            for child in method_parameters.children:
                if child.type == "formal_parameter":
                    parameter_entity = parameterEntity(child)
                    method_entity.set_parameter_entity(parameter_entity)
                    for parameter_child in child.children:
                        if "type" in parameter_child.type:
                            parameter_entity.set_parameter_type(
                                get_parameter_type(parameter_child.text.decode("utf-8"), parameter_entity))
                        elif parameter_child.type == "identifier":
                            parameter_entity.set_parameter_name(parameter_child.text.decode("utf-8"))
        method_signature = ""
        for child in method_node.children:
            if child.type == "modifiers":
                for modifier in child.children:
                    if "annotation" in modifier.type:
                        annotation = modifier.text.decode("utf-8")
                        method_entity.set_annotation(annotation)
                        if annotation == "@Test":
                            method_entity.set_is_test_method()
            if child.type != "block":
                if "parameter" not in child.type and method_signature:
                    method_signature += " " + child.text.decode("utf-8")
                else:
                    method_signature += child.text.decode("utf-8")
            elif child.type == "block":
                parse_java_invoke_method(child, method_entity)
        method_entity.set_method_signature(method_signature)
        method_body = method_node.child_by_field_name("body")
        return method_entity.get_is_test_method() or (method_body.end_point[0] - method_body.start_point[0]) > 10
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {class_entity.get_belong_file().get_file_path()}, skip this file")
    except RecursionError:
        print(f"RecursionError: {class_entity.get_belong_file().get_file_path()}, skip this file")


def parse_java_class(class_entity, file_entity):
    try:
        class_node = class_entity.get_node()
        class_entity.set_belong_file(file_entity)
        class_name = class_node.child_by_field_name("name").text.decode("utf-8")
        class_entity.set_class_name(class_name)
        if class_node.prev_sibling and class_node.prev_sibling.type == "comment":
            comment = class_node.prev_sibling.text.decode("utf-8")
            class_entity.set_comment(comment)
        class_interface = class_node.child_by_field_name("interfaces")
        if class_interface:
            for child in class_interface.children:
                if child.type == "interface_type_list":
                    for interface in child.text.decode("utf-8").split(','):
                        class_entity.set_inheritances_name(interface)
        class_superclass = class_node.child_by_field_name("superclass")
        if class_superclass:
            class_entity.set_inheritances_name(class_superclass.child(1).text.decode("utf-8"))
        class_body = class_node.child_by_field_name("body")
        for child in class_body.children:
            if child.type == "method_declaration":
                if child.child_by_field_name("body"):
                    method_entity = methodEntity(child)
                    if parse_java_method(method_entity, class_entity):
                        class_entity.set_method_entity(method_entity)
            elif child.type == "class_declaration":
                inner_class_entity = classEntity(child)
                class_entity.set_class_entity(inner_class_entity)
                parse_java_class(inner_class_entity, file_entity)
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {file_entity.get_file_path()}, skip this file")
    except RecursionError:
        print(f"RecursionError: {file_entity.get_file_path()}, skip this file")


def parse_java_file(path):
    try:
        with open(path, 'r') as file:
            code = file.read()
            tree = parsers['java'].parse(bytes(code, 'utf8'))
            root = tree.root_node
            file_entity = fileEntity(root)
            file_entity.set_file_name(path.split('/')[-1])
            file_entity.set_file_path(path)
            for child in root.children:
                if child.type == "class_declaration":
                    class_entity = classEntity(child)
                    file_entity.set_class_entity(class_entity)
                    parse_java_class(class_entity, file_entity)
                elif child.type == "import_declaration":
                    for import_package in child.children:
                        if import_package.type == "scoped_identifier":
                            import_package_name = import_package.text.decode("utf-8")
                            file_entity.set_import_text(import_package_name)
                elif child.type == "package_declaration":
                    for package in child.children:
                        if package.type == "scoped_identifier":
                            package_name = package.text.decode("utf-8")
                            file_entity.set_package_text(package_name)
            for class_entity in file_entity.get_class_entity():
                for method_entity in class_entity.get_method_entity():
                    if method_entity.get_is_test_method():
                        file_entity.set_is_test_file()
                        break
                if file_entity.get_is_test_file():
                    break
            for class_entity in file_entity.get_class_entity():
                for method_entity in class_entity.get_method_entity():
                    method_node = method_entity.get_node()
                    file.seek(0)
                    lines = file.readlines()
                    start = method_node.prev_sibling.start_point[0] if method_entity.get_comment() else \
                        method_node.start_point[0]
                    end = method_node.end_point[0] + 1
                    method_entity.set_left_context(''.join(lines[:start]))
                    method_entity.set_right_context(''.join(lines[end:]))
            return file_entity
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {path}, skip this file")
    except RecursionError:
        print(f"RecursionError: {path}, skip this file")


# 解析python文件中的api调用

def analyze_python_function_api(node, import_packages, api_count, apis):
    if node is None:
        return
    for child in node.children:
        if child.type == "call":
            function_name = child.child_by_field_name("function").text.decode("utf-8").split("(")[0]
            key_function_name = function_name.split('.')[0]
            if key_function_name in import_packages.keys():
                api_name = import_packages[key_function_name] + function_name.replace(key_function_name, "", 1)
                for api in apis:
                    flag = True
                    for accept in api["accept"]:
                        if accept not in api_name.lower():
                            flag = False
                            break
                    if not flag:
                        continue
                    for reject in api["reject"]:
                        if reject in api_name.lower():
                            flag = False
                            break
                    if not flag:
                        continue
                    api_count[api["name"]][api_name] += 1
        analyze_python_function_api(child, import_packages, api_count, apis)


def analyze_python_api(path, apis):
    try:
        with open(path, 'r') as file:
            api_count = {}
            for api in apis:
                api_count[api['name']] = Counter()
            import_packages = {}
            code = file.read()
            tree = parsers['python'].parse(bytes(code, 'utf8'))
            root = tree.root_node
            for node in root.children:
                if node.type == "import_from_statement":
                    module = node.child_by_field_name("module_name")
                    if module.type == "dotted_name":
                        module_name = module.text.decode("utf-8")
                        for child in node.children:
                            if child.type == "dotted_name" and child.prev_sibling.type != "from":
                                child_name = child.text.decode("utf-8")
                                import_packages[child_name] = module_name + "." + child_name
                            elif child.type == "aliased_import":
                                child_name = child.child_by_field_name("name").text.decode("utf-8")
                                child_alias = child.child_by_field_name("alias").text.decode("utf-8")
                                import_packages[child_alias] = module_name + "." + child_name
                elif node.type == "import_statement":
                    module = node.child_by_field_name("name")
                    while module is not None:
                        if module.type == "aliased_import":
                            child_name = module.child_by_field_name("name").text.decode("utf-8")
                            child_alias = module.child_by_field_name("alias").text.decode("utf-8")
                            import_packages[child_alias] = child_name
                        elif module.type == "dotted_name":
                            module_name = module.text.decode("utf-8")
                            import_packages[module_name] = module_name
                        module = module.next_named_sibling
                else:
                    analyze_python_function_api(node, import_packages, api_count, apis)
            return api_count

    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {path}, skip this file")
    except RecursionError:
        print(f"RecursionError: {path}, skip this file")


def parse_python_call(node, call_result):
    if node is None:
        return
    if node.type == "call":
        function = node.child_by_field_name("function")
        if function.type == "identifier":
            name = function.text.decode("utf-8")
            argument_list = node.child_by_field_name("arguments")
            argument_count = 0
            for argument in argument_list.children:
                if argument.type != "(" and argument.type != ")" and argument.type != ",":
                    argument_count += 1
            call_result.append(tuple((name, argument_count)))
        else:
            function_name = function.text.decode("utf-8")
            if "(" not in function_name:
                argument_list = node.child_by_field_name("arguments")
                argument_count = 0
                for argument in argument_list.children:
                    if argument.type != "(" and argument.type != ")" and argument.type != ",":
                        argument_count += 1
                call_result.append(tuple((function_name, argument_count)))
            else:
                for function_child in function.children:
                    if function_child.type == "identifier":
                        name = function_child.text.decode("utf-8")
                        argument_list = node.child_by_field_name("arguments")
                        argument_count = 0
                        for argument in argument_list.children:
                            if argument.type != "(" and argument.type != ")" and argument.type != ",":
                                argument_count += 1
                        call_result.append(tuple((name, argument_count)))
                    else:
                        parse_python_call(function_child, call_result)
    else:
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode("utf-8")
                # if node.type == "call":
                #     argument_list = node.child_by_field_name("arguments")
                #     call_result.append(tuple((name, argument_list)))
                if node.type == "attribute":
                    call_result.append(tuple((name, 0)))
            else:
                parse_python_call(child, call_result)


def parse_python_function_body(node, function_entity):
    if node is None:
        return
    for child in node.children:
        if child.type == "call":
            key_method_name = child.child_by_field_name("function").text.decode("utf-8").split('(')[0].split(".")[0]
            function_variable = function_entity.get_variables()
            file_variable = function_entity.get_belong_file().get_variables()
            flag = False
            call_api = ""
            if key_method_name in function_variable.keys():
                call_api = function_variable[key_method_name]
                flag = True
            elif key_method_name in file_variable.keys():
                call_api = file_variable[key_method_name]
                flag = True
            if flag:
                call_result = []
                parse_python_call(child, call_result)
                if call_result:
                    first_call = call_result[0]
                    first_call_name = first_call[0].replace(key_method_name, "", 1)
                    call_api = call_api + first_call_name
                    call_entity = pythonCallEntity(child)
                    function_entity.set_call_method(call_entity)
                    call_entity.set_call_api(call_api)
                    call_entity.set_belong_function(function_entity)
                    call_entity.set_parameter(first_call[1])
                    for i in range(1, len(call_result)):
                        call_api = call_api + "." + call_result[i][0]
                        call_entity = pythonCallEntity(child)
                        function_entity.set_call_method(call_entity)
                        call_entity.set_call_api(call_api)
                        call_entity.set_belong_function(function_entity)
                        call_entity.set_parameter(call_result[i][1])
                    if node.type == "assignment":
                        left = node.child_by_field_name("left")
                        if left.type == "identifier":
                            function_entity.set_variables(left.text.decode("utf-8"), call_api)
        parse_python_function_body(child, function_entity)


def parse_python_function(node, function_entity):
    function_name = node.child_by_field_name("name").text.decode("utf-8")
    function_body = node.child_by_field_name("body")
    function_parameters = node.child_by_field_name("parameters")
    function_entity.set_function_name(function_name)
    function_signature = function_name + function_parameters.text.decode("utf-8")
    function_entity.set_function_signature(function_signature)
    if function_name.lower().startswith("test") or function_name.lower().endswith("test"):
        function_entity.set_is_test_function()
        function_entity.get_belong_file().set_is_test_file()
        if function_entity.get_belong_class():
            function_entity.get_belong_class().set_is_test_class()
    for child in function_parameters.children:
        if child.type == "identifier":
            if child.text.decode("utf-8") == "self":
                continue
            else:
                parameter_entity = parameterEntity(child)
                function_entity.set_parameter_entity(parameter_entity)
                parameter_entity.set_parameter_name(child.text.decode("utf-8"))
    start = function_body.start_point[0]
    end = function_body.end_point[0]
    if function_child := function_body.child(0):
        if function_child.type == "expression_statement":
            if comment := function_child.child(0):
                if comment.type == "string":
                    function_entity.set_comment(comment.text.decode("utf-8"))
                    start = comment.start_point[0]
    if function_entity.get_is_test_function() or (end - start) > 10:
        parse_python_function_body(function_body, function_entity)
        return True
    else:
        return False


def parse_python_class(node, class_entity):
    class_name = node.child_by_field_name("name").text.decode("utf-8")
    class_body = node.child_by_field_name("body")
    class_entity.set_class_name(class_name)
    if class_name.lower().startswith("test") or class_name.lower().endswith("test"):
        class_entity.set_is_test_class()
        class_entity.get_belong_file().set_is_test_file()
    for child in class_body.children:
        if child.type == "function_definition":
            function_name = child.child_by_field_name("name").text.decode("utf-8")
            if function_name.startswith("__") and function_name.endswith("__"):
                continue
            else:
                function_entity = pythonFunctionEntity(child)
                function_entity.set_belong_class(class_entity)
                function_entity.set_belong_file(class_entity.get_belong_file())
                if parse_python_function(child, function_entity):
                    class_entity.set_function_entity(function_entity)
        elif child.type == "decorated_definition":
            body_node = child.child_by_field_name("definition")
            function_entity = pythonFunctionEntity(body_node)
            function_entity.set_belong_class(class_entity)
            function_entity.set_belong_file(class_entity.get_belong_file())
            if parse_python_function(body_node, function_entity):
                class_entity.set_function_entity(function_entity)
                for children in child.children:
                    if children.type == "decorator":
                        decorator = children.text.decode("utf-8")
                        function_entity.set_decorator(decorator)


def parse_python_file(path):
    try:
        with open(path, 'r') as file:
            code = file.read()
            tree = parsers['python'].parse(bytes(code, 'utf-8'))
            root = tree.root_node
            file_entity = fileEntity(root)
            file_entity.set_file_name(path.split('/')[-1])
            file_entity.set_file_path(path)
            file_name = file_entity.get_file_name()
            if file_name.lower().startswith("test") or file_name.lower().endswith("test"):
                file_entity.set_is_test_file()
            for node in root.children:
                if node.type == "import_from_statement":
                    module = node.child_by_field_name("module_name")
                    if module.type == "dotted_name":
                        module_name = module.text.decode("utf-8")
                        for child in node.children:
                            if child.type == "dotted_name" and child.prev_sibling.type != "from":
                                child_name = child.text.decode("utf-8")
                                file_entity.set_import_text(module_name + "." + child_name)
                                file_entity.set_variables(child_name, module_name + "." + child_name)
                            elif child.type == "aliased_import":
                                child_name = child.child_by_field_name("name").text.decode("utf-8")
                                child_alias = child.child_by_field_name("alias").text.decode("utf-8")
                                file_entity.set_import_text(module_name + "." + child_name)
                                file_entity.set_variables(child_alias, module_name + "." + child_name)
                    elif module.type == "relative_import":
                        module_name = module.text.decode("utf-8")
                        if module_name == ".":
                            module_name = path.split('/')[-2]
                        elif module_name == "..":
                            module_name = path.split('/')[-3]
                        else:
                            continue
                        for child in node.children:
                            if child.type == "dotted_name":
                                child_name = child.text.decode("utf-8")
                                file_entity.set_variables(child_name, module_name + "." + child_name)
                            elif child.type == "aliased_import":
                                child_name = child.child_by_field_name("name").text.decode("utf-8")
                                child_alias = child.child_by_field_name("alias").text.decode("utf-8")
                                file_entity.set_variables(child_alias, module_name + "." + child_name)
                elif node.type == "import_statement":
                    module = node.child_by_field_name("name")
                    while module is not None:
                        if module.type == "aliased_import":
                            child_name = module.child_by_field_name("name").text.decode("utf-8")
                            child_alias = module.child_by_field_name("alias").text.decode("utf-8")
                            file_entity.set_import_text(child_name)
                            file_entity.set_variables(child_alias, child_name)
                        elif module.type == "dotted_name":
                            module_name = module.text.decode("utf-8")
                            file_entity.set_import_text(module_name)
                            file_entity.set_variables(module_name, module_name)
                        module = module.next_named_sibling
                elif node.type == "function_definition":
                    function_entity = pythonFunctionEntity(node)
                    file_entity.set_function_entity(function_entity)
                    function_entity.set_belong_file(file_entity)
                    parse_python_function(node, function_entity)
                elif node.type == "class_definition":
                    class_entity = pythonClassEntity(node)
                    file_entity.set_class_entity(class_entity)
                    class_entity.set_belong_file(file_entity)
                    parse_python_class(node, class_entity)
                elif node.type == "decorated_definition":
                    body_node = node.child_by_field_name("definition")
                    if body_node.type == "function_definition":
                        function_entity = pythonFunctionEntity(body_node)
                        file_entity.set_function_entity(function_entity)
                        function_entity.set_belong_file(file_entity)
                        parse_python_function(body_node, function_entity)
                    elif body_node.type == "class_definition":
                        class_entity = pythonClassEntity(body_node)
                        file_entity.set_class_entity(class_entity)
                        class_entity.set_belong_file(file_entity)
                        parse_python_class(body_node, class_entity)
                    for child in node.children:
                        if child.type == "decorator":
                            decorator = child.text.decode("utf-8")
                            if body_node.type == "function_definition":
                                function_entity.set_decorator(decorator)
                            elif body_node.type == "class_definition":
                                class_entity.set_decorator(decorator)
            for class_entity in file_entity.get_class_entity():
                if class_entity:
                    for function_entity in class_entity.get_function_entity():
                        function_node = function_entity.get_node()
                        file.seek(0)
                        lines = file.readlines()
                        start = function_node.start_point[0]
                        end = function_node.end_point[0] + 1
                        function_entity.set_left_context(''.join(lines[:start]))
                        function_entity.set_right_context(''.join(lines[end:]))
            for function_entity in file_entity.get_function_entity():
                function_node = function_entity.get_node()
                file.seek(0)
                lines = file.readlines()
                start = function_node.start_point[0]
                end = function_node.end_point[0] + 1
                function_entity.set_left_context(''.join(lines[:start]))
                function_entity.set_right_context(''.join(lines[end:]))
            return file_entity
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {path}, skip this file")
    except RecursionError:
        print(f"RecursionError: {path}, skip this file")
