# 提取Java文件中的方法和测试方法对


def match_same_contain_method(test_file_parser, file_parser):
    for test_class_entity in test_file_parser.get_class_entity():
        for test_method_entity in test_class_entity.get_method_entity():
            test_method_name = (
                test_method_entity.get_method_name()
                .lower()
                .replace("test", "")
                .replace("tests", "")
            )
            for class_entity in file_parser.get_class_entity():
                for method_entity in class_entity.get_method_entity():
                    method_name = method_entity.get_method_name().lower()
                    if method_name in test_method_name:
                        for test_call_method in test_method_entity.get_call_method():
                            test_call_method_name = (
                                test_call_method.get_call_method_name()
                                .split(".")[-1]
                                .lower()
                            )
                            if test_call_method_name == method_name:
                                test_parameter = test_call_method.get_parameter_entity()
                                parameter = method_entity.get_parameter_entity()
                                if len(test_parameter) == len(parameter):
                                    import_texts = file_parser.get_import_text()
                                    flag = False
                                    for (
                                        invocation_method
                                    ) in method_entity.get_call_method():
                                        for import_text in import_texts:
                                            if (
                                                invocation_method.get_call_method_name().split(
                                                    "."
                                                )[
                                                    0
                                                ]
                                                == import_text.split(".")[-1]
                                            ):
                                                flag = True
                                                break
                                        if flag:
                                            break
                                    if flag:
                                        yield (test_method_entity, method_entity)
                                        break


def match_methods_and_tests(file_parsers):
    match_result = {}
    for test_file_parser in file_parsers:
        if not test_file_parser:
            continue
        if test_file_parser.get_is_test_file():
            for file_parser in file_parsers:
                if not file_parser:
                    continue
                if file_parser.get_is_test_file():
                    continue
                if not (
                    file_parser.get_file_name().replace(".java", "")
                    in test_file_parser.get_file_name().replace(".java", "")
                    and test_file_parser.get_package_text()
                    == file_parser.get_package_text()
                ):
                    continue
                for test_call_method, method_entity in match_same_contain_method(
                    test_file_parser, file_parser
                ):
                    if method_entity in match_result.keys():
                        match_result[method_entity].append(test_call_method)
                    else:
                        match_result[method_entity] = [test_call_method]
    # 内存优化
    for file_entity in file_parsers:
        if not file_entity:
            continue
        file_entity.clear_index()
    return match_result
