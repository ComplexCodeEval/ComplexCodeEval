# 将Python代码文件解析成语法树的相关工具

from collections import Counter

from tree_sitter import Language, Parser
from dataset_extract.Entity.file_entity import fileEntity
from dataset_extract.Entity.parameter_entity import parameterEntity
from dataset_extract.Entity.python_function_entity import pythonFunctionEntity
from dataset_extract.Entity.python_class_entity import pythonClassEntity
from dataset_extract.Entity.python_call_entity import pythonCallEntity

parsers = {}

for lang in ["python"]:
    LANGUAGE = Language("./dataset_extract/parser/my-languages.so", lang)
    parser = Parser()
    parser.set_language(LANGUAGE)
    parsers[lang] = parser


# 测试code file是否存在语法错误
def test_error(root):
    try:
        if root is None:
            return False
        if root.type == "ERROR":
            return True
        for child in root.children:
            if test_error(child):
                return True
        return False
    except RecursionError:
        return True


def analyze_python_function_api(node, import_packages, api_count, apis):
    if node is None:
        return
    for child in node.children:
        if child.type == "call":
            function_name = (
                child.child_by_field_name("function").text.decode("utf-8").split("(")[0]
            )
            key_function_name = function_name.split(".")[0]
            if key_function_name in import_packages.keys():
                api_name = import_packages[key_function_name] + function_name.replace(
                    key_function_name, "", 1
                )
                for api in apis:
                    flag = False
                    for accept in api["accept"]:
                        if api_name.lower().startswith(accept):
                            flag = True
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
        with open(path, "r") as file:
            api_count = {}
            for api in apis:
                api_count[api["name"]] = Counter()
            import_packages = {}
            code = file.read()
            tree = parsers["python"].parse(bytes(code, "utf8"))
            root = tree.root_node
            for node in root.children:
                if node.type == "import_from_statement":
                    module = node.child_by_field_name("module_name")
                    if module.type == "dotted_name":
                        module_name = module.text.decode("utf-8")
                        for child in node.children:
                            if (
                                child.type == "dotted_name"
                                and child.prev_sibling.type != "from"
                            ):
                                child_name = child.text.decode("utf-8")
                                import_packages[child_name] = (
                                    module_name + "." + child_name
                                )
                            elif child.type == "aliased_import":
                                child_name = child.child_by_field_name(
                                    "name"
                                ).text.decode("utf-8")
                                child_alias = child.child_by_field_name(
                                    "alias"
                                ).text.decode("utf-8")
                                import_packages[child_alias] = (
                                    module_name + "." + child_name
                                )
                elif node.type == "import_statement":
                    module = node.child_by_field_name("name")
                    while module is not None:
                        if module.type == "aliased_import":
                            child_name = module.child_by_field_name("name").text.decode(
                                "utf-8"
                            )
                            child_alias = module.child_by_field_name(
                                "alias"
                            ).text.decode("utf-8")
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
                if (
                    argument.type != "("
                    and argument.type != ")"
                    and argument.type != ","
                ):
                    argument_count += 1
            call_result.append(tuple((name, argument_count)))
        else:
            function_name = function.text.decode("utf-8")
            if "(" not in function_name:
                argument_list = node.child_by_field_name("arguments")
                argument_count = 0
                for argument in argument_list.children:
                    if (
                        argument.type != "("
                        and argument.type != ")"
                        and argument.type != ","
                    ):
                        argument_count += 1
                call_result.append(tuple((function_name, argument_count)))
            else:
                for function_child in function.children:
                    if function_child.type == "identifier":
                        name = function_child.text.decode("utf-8")
                        argument_list = node.child_by_field_name("arguments")
                        argument_count = 0
                        for argument in argument_list.children:
                            if (
                                argument.type != "("
                                and argument.type != ")"
                                and argument.type != ","
                            ):
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
            key_method_name = (
                child.child_by_field_name("function")
                .text.decode("utf-8")
                .split("(")[0]
                .split(".")[0]
            )
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
                            function_entity.set_variables(
                                left.text.decode("utf-8"), call_api
                            )
        parse_python_function_body(child, function_entity)


def parse_python_function(node, function_entity):
    function_name = node.child_by_field_name("name").text.decode("utf-8")
    function_body = node.child_by_field_name("body")
    if not function_body:
        return False
    function_parameters = node.child_by_field_name("parameters")
    function_entity.set_function_name(function_name)
    # function_signature = function_name + function_parameters.text.decode("utf-8")
    # function_entity.set_function_signature(function_signature)
    function_signature = ""
    for child in node.children:
        if child.type != "block":
            if "comment" in child.type:
                continue
            elif "parameter" not in child.type and function_signature:
                function_signature += " " + child.text.decode("utf-8")
            else:
                function_signature += child.text.decode("utf-8")
    function_entity.set_function_signature(function_signature)
    if function_name.lower().startswith("test") or function_name.lower().endswith(
        "test"
    ):
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
    if end - start < 10:
        return False
    function_entity.set_left_context(node.start_point[0])
    function_entity.set_right_context(node.end_point[0] + 1)
    function_entity.set_comment(tuple((node.start_point[0], node.start_point[0])))
    if function_child := function_body.child(0):
        if function_child.type == "expression_statement":
            if comment := function_child.child(0):
                if comment.type == "string":
                    function_entity.set_comment(
                        tuple((comment.start_point[0], comment.end_point[0] + 1))
                    )
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
    if not class_body:
        return
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
            if body_node.type == "function_definition":
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
        with open(path, "r") as file:
            code = file.read()
            tree = parsers["python"].parse(bytes(code, "utf-8"))
            root = tree.root_node
            if test_error(root):
                return
            file_entity = fileEntity(root)
            file_entity.set_file_name(path.split("/")[-1])
            file_entity.set_file_path(path)
            file_name = file_entity.get_file_name()
            if file_name.lower().startswith("test") or file_name.lower().endswith(
                "test.py"
            ):
                file_entity.set_is_test_file()
            try:
                for node in root.children:
                    if node.type == "import_from_statement":
                        module = node.child_by_field_name("module_name")
                        if module.type == "dotted_name":
                            module_name = module.text.decode("utf-8")
                            for child in node.children:
                                if (
                                    child.type == "dotted_name"
                                    and child.prev_sibling.type != "from"
                                ):
                                    child_name = child.text.decode("utf-8")
                                    file_entity.set_import_text(
                                        module_name + "." + child_name
                                    )
                                    file_entity.set_variables(
                                        child_name, module_name + "." + child_name
                                    )
                                elif child.type == "aliased_import":
                                    child_name = child.child_by_field_name(
                                        "name"
                                    ).text.decode("utf-8")
                                    child_alias = child.child_by_field_name(
                                        "alias"
                                    ).text.decode("utf-8")
                                    file_entity.set_import_text(
                                        module_name + "." + child_name
                                    )
                                    file_entity.set_variables(
                                        child_alias, module_name + "." + child_name
                                    )
                        elif module.type == "relative_import":
                            module_name = module.text.decode("utf-8")
                            if module_name == ".":
                                module_name = path.split("/")[-2]
                            elif module_name == "..":
                                module_name = path.split("/")[-3]
                            else:
                                continue
                            for child in node.children:
                                if child.type == "dotted_name":
                                    child_name = child.text.decode("utf-8")
                                    file_entity.set_variables(
                                        child_name, module_name + "." + child_name
                                    )
                                elif child.type == "aliased_import":
                                    child_name = child.child_by_field_name(
                                        "name"
                                    ).text.decode("utf-8")
                                    child_alias = child.child_by_field_name(
                                        "alias"
                                    ).text.decode("utf-8")
                                    file_entity.set_variables(
                                        child_alias, module_name + "." + child_name
                                    )
                    elif node.type == "import_statement":
                        module = node.child_by_field_name("name")
                        while module is not None:
                            if module.type == "aliased_import":
                                child_name = module.child_by_field_name(
                                    "name"
                                ).text.decode("utf-8")
                                child_alias = module.child_by_field_name(
                                    "alias"
                                ).text.decode("utf-8")
                                file_entity.set_import_text(child_name)
                                file_entity.set_variables(child_alias, child_name)
                            elif module.type == "dotted_name":
                                module_name = module.text.decode("utf-8")
                                file_entity.set_import_text(module_name)
                                file_entity.set_variables(module_name, module_name)
                            module = module.next_named_sibling
                    elif node.type == "function_definition":
                        function_entity = pythonFunctionEntity(node)
                        function_entity.set_belong_file(file_entity)
                        if parse_python_function(node, function_entity):
                            file_entity.set_function_entity(function_entity)
                    elif node.type == "class_definition":
                        class_entity = pythonClassEntity(node)
                        file_entity.set_class_entity(class_entity)
                        class_entity.set_belong_file(file_entity)
                        parse_python_class(node, class_entity)
                    elif node.type == "decorated_definition":
                        body_node = node.child_by_field_name("definition")
                        if body_node.type == "function_definition":
                            function_entity = pythonFunctionEntity(body_node)
                            function_entity.set_belong_file(file_entity)
                            if parse_python_function(body_node, function_entity):
                                file_entity.set_function_entity(function_entity)
                                for children in node.children:
                                    if children.type == "decorator":
                                        decorator = children.text.decode("utf-8")
                                        function_entity.set_decorator(decorator)
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
            except RecursionError:
                file_entity.clear_node()
                file_entity.clear_index()
                print(f"RecursionError: {path}, skip this file")
                file.close()
                return
            # 内存优化
            file_entity.clear_node()
            return file_entity
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {path}, skip this file")
