# 将Java代码文件解析成语法树的相关工具

from collections import Counter

from tree_sitter import Language, Parser
from dataset_extract.Entity.file_entity import fileEntity
from dataset_extract.Entity.class_entity import classEntity
from dataset_extract.Entity.method_entity import methodEntity
from dataset_extract.Entity.call_method_entity import callMethodEntity
from dataset_extract.Entity.parameter_entity import parameterEntity

parsers = {}

for lang in ["java"]:
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
            invocation_name = child.text.decode("utf-8").split("(")[0].split(".")
            if invocation_name[0] in import_packages.keys():
                if len(invocation_name) > 1:
                    api_name = (
                        import_packages[invocation_name[0]]
                        + "."
                        + ".".join(invocation_name[1:])
                    )
                else:
                    api_name = import_packages[invocation_name[0]]
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
        analyze_java_method_api(child, method, import_packages, api_count, apis)


def analyze_java_api(path, apis):
    try:
        with open(path, "r") as file:
            api_count = {}
            for api in apis:
                api_count[api["name"]] = Counter()
            import_packages = {}
            code = file.read()
            tree = parsers["java"].parse(bytes(code, "utf8"))
            root = tree.root_node
            for child in root.children:
                if child.type == "import_declaration":
                    for import_package in child.children:
                        if import_package.type == "scoped_identifier":
                            import_package_name = import_package.text.decode("utf-8")
                            import_class_name = import_package_name.split(".")[-1]
                            import_packages[import_class_name] = import_package_name
                if child.type == "class_declaration":
                    for class_body in analyze_java_class(child):
                        for node in class_body.children:
                            if node.type == "method_declaration":
                                method_name = node.child_by_field_name(
                                    "name"
                                ).text.decode("utf-8")
                                analyze_java_method_api(
                                    node, method_name, import_packages, api_count, apis
                                )
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
        return get_parameter_type(
            "".join(parameter_type.split("<")[0]), parameter_entity
        )
    if "." in parameter_type:
        return get_parameter_type(
            "".join(parameter_type.split(".")[-1]), parameter_entity
        )
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
            call_method_name = child.text.decode("utf-8").split("(")[0]
            call_method_entity.set_call_method_name(call_method_name)
            for call_method_child in child.children:
                if call_method_child.type == "argument_list":
                    for argument_child in call_method_child.children:
                        if (
                            argument_child.type != "("
                            and argument_child.type != ")"
                            and argument_child.type != ","
                        ):
                            parameter_entity = parameterEntity(argument_child)
                            parameter_entity.set_parameter_type(argument_child.type)
                            parameter_entity.set_parameter_name(
                                argument_child.text.decode("utf-8")
                            )
                            call_method_entity.set_parameter_entity(parameter_entity)
        parse_java_invoke_method(child, method_entity)


def parse_java_method(method_entity, class_entity):
    method_node = method_entity.get_node()
    method_entity.set_belong_class(class_entity)
    method_name = method_node.child_by_field_name("name").text.decode("utf-8")
    method_entity.set_method_name(method_name)
    method_entity.set_left_context(method_node.start_point[0])
    method_entity.set_right_context(method_node.end_point[0] + 1)
    if method_node.prev_sibling and method_node.prev_sibling.type == "block_comment":
        comment_node = method_node.prev_sibling
        comment = tuple((comment_node.start_point[0], comment_node.end_point[0] + 1))
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
                            get_parameter_type(
                                parameter_child.text.decode("utf-8"), parameter_entity
                            )
                        )
                    elif parameter_child.type == "identifier":
                        parameter_entity.set_parameter_name(
                            parameter_child.text.decode("utf-8")
                        )
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
    return (
        method_entity.get_is_test_method()
        or (method_body.end_point[0] - method_body.start_point[0]) > 10
    )


def parse_java_class(class_entity, file_entity):
    class_node = class_entity.get_node()
    class_entity.set_belong_file(file_entity)
    class_name = class_node.child_by_field_name("name").text.decode("utf-8")
    class_entity.set_class_name(class_name)
    if class_node.prev_sibling and class_node.prev_sibling.type == "block_comment":
        comment = class_node.prev_sibling.text.decode("utf-8")
        class_entity.set_comment(comment)
    class_interface = class_node.child_by_field_name("interfaces")
    if class_interface:
        for child in class_interface.children:
            if child.type == "interface_type_list":
                for interface in child.text.decode("utf-8").split(","):
                    class_entity.set_inheritances_name(interface)
    class_superclass = class_node.child_by_field_name("superclass")
    if class_superclass:
        class_entity.set_inheritances_name(
            class_superclass.child(1).text.decode("utf-8")
        )
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


def parse_java_file(path):
    try:
        with open(path, "r") as file:
            code = file.read()
            tree = parsers["java"].parse(bytes(code, "utf8"))
            root = tree.root_node
            if test_error(root):
                return
            file_entity = fileEntity(root)
            file_entity.set_file_name(path.split("/")[-1])
            file_entity.set_file_path(path)
            try:
                for child in root.children:
                    if child.type == "class_declaration":
                        class_entity = classEntity(child)
                        file_entity.set_class_entity(class_entity)
                        parse_java_class(class_entity, file_entity)
                    elif child.type == "import_declaration":
                        for import_package in child.children:
                            if import_package.type == "scoped_identifier":
                                import_package_name = import_package.text.decode(
                                    "utf-8"
                                )
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
