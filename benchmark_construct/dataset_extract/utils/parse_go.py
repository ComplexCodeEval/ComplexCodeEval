# 将Go代码文件解析成语法树的相关工具

from collections import Counter
from tree_sitter import Language, Parser

from dataset_extract.Entity.file_entity import fileEntity
from dataset_extract.Entity.go_function_entity import goFunctionEntity
from dataset_extract.Entity.go_call_entity import goCallEntity
from dataset_extract.Entity.parameter_entity import parameterEntity


parsers = {}

for lang in ["go"]:
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


def analyze_go_function_api(node, import_packages, api_count, apis):
    if node is None:
        return
    for child in node.children:
        if child.type == "call_expression":
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
        analyze_go_function_api(child, import_packages, api_count, apis)


def analyze_go_api(path, apis):
    try:
        with open(path, "r") as file:
            api_count = {}
            for api in apis:
                api_count[api["name"]] = Counter()
            import_packages = {}
            code = file.read()
            tree = parsers["go"].parse(bytes(code, "utf8"))
            root = tree.root_node
            for node in root.children:
                if node.type == "import_declaration":
                    for child in node.children:
                        if child.type == "import_spec":
                            api = child.text.decode("utf-8").split('"')[1]
                            package = child.child_by_field_name("name")
                            if (
                                package is not None
                                and package.type == "package_identifier"
                            ):
                                package_name = package.text.decode("utf-8")
                                import_packages[package_name] = api
                            else:
                                import_packages[api.split("/")[-1]] = api
                        elif child.type == "import_spec_list":
                            for import_spec in child.children:
                                if import_spec.type == "import_spec":
                                    try:
                                        api = import_spec.text.decode("utf-8").split(
                                            '"'
                                        )[1]
                                    except IndexError:
                                        api = import_spec.text.decode("utf-8").split(
                                            "`"
                                        )[1]
                                    package = import_spec.child_by_field_name("name")
                                    if (
                                        package is not None
                                        and package.type == "package_identifier"
                                    ):
                                        package_name = package.text.decode("utf-8")
                                        import_packages[package_name] = api
                                    else:
                                        import_packages[api.split("/")[-1]] = api
                else:
                    analyze_go_function_api(node, import_packages, api_count, apis)
            return api_count
    except Exception as e:
        print("--->Error: ", e)


def parse_go_call(node, call_result):
    if node is None:
        return
    if node.type == "call_expression":
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
                        parse_go_call(function_child, call_result)
    else:
        for child in node.children:
            parse_go_call(child, call_result)


def parse_go_function_body(node, function_entity):
    stack = [node]
    while stack:
        current_node = stack.pop()
        if current_node.type == "call_expression":
            key_method_name = (
                current_node.child_by_field_name("function")
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
                parse_go_call(current_node, call_result)
                if call_result:
                    first_call = call_result[0]
                    first_call_name = first_call[0].replace(key_method_name, "", 1)
                    call_api = call_api + first_call_name
                    call_entity = goCallEntity(current_node)
                    function_entity.set_call_method(call_entity)
                    call_entity.set_call_api(call_api)
                    call_entity.set_belong_function(function_entity)
                    call_entity.set_parameter(first_call[1])
                    for i in range(1, len(call_result)):
                        call_api = call_api + "." + call_result[i][0]
                        call_entity = goCallEntity(current_node)
                        function_entity.set_call_method(call_entity)
                        call_entity.set_call_api(call_api)
                        call_entity.set_belong_function(function_entity)
                        call_entity.set_parameter(call_result[i][1])
                    if current_node.type == "assignment_statement":
                        left = current_node.child_by_field_name("left")
                        if left.type == "identifier":
                            function_entity.set_variables(
                                left.text.decode("utf-8"), call_api
                            )
        stack.extend(reversed(current_node.children))


def parse_go_function(node, function_entity):
    function_name = node.child_by_field_name("name").text.decode("utf-8")
    function_body = node.child_by_field_name("body")
    if not function_body:
        return False
    function_parameters = node.child_by_field_name("parameters")
    function_receiver = node.child_by_field_name("receiver")
    function_entity.set_function_name(function_name)
    if function_receiver:
        for child in function_receiver.children:
            if child.type == "parameter_declaration":
                class_name = child.child_by_field_name("type").text.decode("utf-8")
                function_entity.set_belong_class(class_name)
    function_signature = ""
    for child in node.children:
        if child.type != "block":
            if "parameter" not in child.type and function_signature:
                function_signature += " " + child.text.decode("utf-8")
            else:
                function_signature += child.text.decode("utf-8")
    function_entity.set_function_signature(function_signature)
    if function_name.lower().startswith("test") or function_name.lower().endswith(
        "test"
    ):
        function_entity.set_is_test_function()
        function_entity.get_belong_file().set_is_test_file()
    for param in function_parameters.children:
        if param.type == "parameter_declaration":
            param_entity = parameterEntity(param)
            try:
                param_name = param.child_by_field_name("name").text.decode("utf-8")
                param_type = param.child_by_field_name("type").text.decode("utf-8")
            except:
                param_name = None
                param_type = param.child_by_field_name("type").text.decode("utf-8")
            function_entity.set_parameter_entity(param_entity)
            param_entity.set_parameter_name(param_name)
            param_entity.set_parameter_type(param_type)
    function_entity.set_left_context(node.start_point[0])
    function_entity.set_right_context(node.end_point[0] + 1)
    comment_node = node.prev_sibling
    start, end = node.start_point[0], node.end_point[0]
    while comment_node and comment_node.type == "comment":
        start = comment_node.start_point[0]
        comment_node = comment_node.prev_sibling
    function_entity.set_comment((start, end))
    parse_go_function_body(function_body, function_entity)
    return (
        function_entity.get_is_test_function()
        or (function_body.end_point[0] - function_body.start_point[0]) > 10
    )


def parse_go_file(file_path):
    try:
        with open(file_path, "r") as file:
            code = file.read()
            tree = parsers["go"].parse(bytes(code, "utf8"))
            root = tree.root_node
            if test_error(root):
                print(f"Syntax error in file: {file_path}")
                return
            file_entity = fileEntity(root)
            file_entity.set_file_name(file_path.split("/")[-1])
            file_entity.set_file_path(file_path)
            file_name = file_entity.get_file_name()
            if file_name.lower().startswith("test") or file_name.lower().endswith(
                "test.go"
            ):
                file_entity.set_is_test_file()
            try:
                for node in root.children:
                    if node.type == "package_clause":
                        for child in node.children:
                            if child.type == "package_identifier":
                                file_entity.set_package_text(child.text.decode("utf-8"))
                    elif node.type == "import_declaration":
                        for child in node.children:
                            if child.type == "import_spec":
                                file_entity.set_import_text(child.text.decode("utf-8"))
                                try:
                                    api = child.text.decode("utf-8").split('"')[1]
                                except IndexError:
                                    api = child.text.decode("utf-8").split("`")[1]
                                package = child.child_by_field_name("name")
                                if (
                                    package is not None
                                    and package.type == "package_identifier"
                                ):
                                    package_name = package.text.decode("utf-8")
                                    file_entity.set_variables(package_name, api)
                                else:
                                    file_entity.set_variables(api.split("/")[-1], api)
                            elif child.type == "import_spec_list":
                                for import_spec in child.children:
                                    if import_spec.type == "import_spec":
                                        file_entity.set_import_text(
                                            import_spec.text.decode("utf-8")
                                        )
                                        try:
                                            api = import_spec.text.decode(
                                                "utf-8"
                                            ).split('"')[1]
                                        except IndexError:
                                            api = import_spec.text.decode(
                                                "utf-8"
                                            ).split("`")[1]
                                        package = import_spec.child_by_field_name(
                                            "name"
                                        )
                                        if (
                                            package is not None
                                            and package.type == "package_identifier"
                                        ):
                                            package_name = package.text.decode("utf-8")
                                            file_entity.set_variables(package_name, api)
                                        else:
                                            file_entity.set_variables(
                                                api.split("/")[-1], api
                                            )
                    elif (
                        node.type == "function_declaration"
                        or node.type == "method_declaration"
                    ):
                        function_entity = goFunctionEntity(node)
                        function_entity.set_belong_file(file_entity)
                        if parse_go_function(node, function_entity):
                            file_entity.set_function_entity(function_entity)
            except RecursionError:
                file_entity.clear_node()
                file_entity.clear_index()
                print(f"RecursionError: {file_path}, skip this file")
                file.close()
                return
            # 内存优化
            file_entity.clear_node()
            return file_entity
    except Exception as e:
        print("--->Error: ", e)
