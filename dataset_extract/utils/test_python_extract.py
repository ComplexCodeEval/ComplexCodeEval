# 提取python文件中的函数和测试函数对

def match_function_and_test(test_function_entity, function_entity):
    class_entity = function_entity.get_belong_class()
    file_entity = function_entity.get_belong_file()
    file_path = file_entity.get_file_path().replace("/", ".").replace(".py", "")
    if class_entity:
        function_path = file_path + "." + class_entity.get_class_name() + "." + function_entity.get_function_name()
    else:
        function_path = file_path + "." + function_entity.get_function_name()
    for call_method in test_function_entity.get_call_method():
        if function_path.endswith(call_method.get_call_api()):
            if len(function_entity.get_call_method()) > 0:
                return True
    return False


def match_file_function(test_function_entity, file_parser):
    for class_entity in file_parser.get_class_entity():
        if not class_entity:
            continue
        for function_entity in class_entity.get_function_entity():
            if match_function_and_test(test_function_entity, function_entity):
                yield function_entity
    for function_entity in file_parser.get_function_entity():
        if match_function_and_test(test_function_entity, function_entity):
            yield function_entity


def match_same_contain_function(test_file_parser, file_parser):
    for test_class_entity in test_file_parser.get_class_entity():
        if not test_class_entity:
            continue
        if test_class_entity.get_is_test_class():
            for test_function_entity in test_class_entity.get_function_entity():
                if test_function_entity.get_is_test_function():
                    for function_entity in match_file_function(test_function_entity, file_parser):
                        yield test_function_entity, function_entity
    for test_function_entity in test_file_parser.get_function_entity():
        if test_function_entity.get_is_test_function():
            for function_entity in match_file_function(test_function_entity, file_parser):
                yield test_function_entity, function_entity


def match_functions_and_tests(file_parsers):
    match_result = {}
    for test_file_parser in file_parsers:
        if test_file_parser:
            if test_file_parser.get_is_test_file():
                import_texts = test_file_parser.get_import_text()
                import_name = []
                for import_text in import_texts:
                    for text in import_text.split("."):
                        import_name.append(text)
                for file_parser in file_parsers:
                    if file_parser:
                        if file_parser.get_is_test_file():
                            continue
                        if not (file_parser.get_file_name().replace(".py", "")
                                in test_file_parser.get_file_name().replace(".py", "")
                                and file_parser.get_file_name().replace(".py", "") in import_name):
                            continue
                        for test_function_entity, function_entity in match_same_contain_function(test_file_parser,
                                                                                                 file_parser):
                            if function_entity in match_result.keys():
                                match_result[function_entity].append(test_function_entity)
                            else:
                                match_result[function_entity] = [test_function_entity]
    return match_result
