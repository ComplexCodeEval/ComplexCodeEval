# 提取Go文件中的方法和测试方法对


def match_same_contain_method(test_file_parser, file_parser):
    for test_function_entity in test_file_parser.get_function_entity():
        test_method_name = (
            test_function_entity.get_function_name().replace("Test", "").lower()
        )
        for function_entity in file_parser.get_function_entity():
            method_name = function_entity.get_function_name().lower()
            if method_name in test_method_name:
                for test_call_method in test_function_entity.get_call_method():
                    test_call_method_name = (
                        test_call_method.get_call_api().split(".")[-1].lower()
                    )
                    if test_call_method_name == method_name:
                        test_parameter_len = test_call_method.get_parameter()
                        parameter = function_entity.get_parameter()
                        if test_parameter_len == len(parameter):
                            yield (test_function_entity, function_entity)
                            break


def match_go_methods_and_tests(file_parsers):
    try:
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
                    if file_parser.get_file_name().replace(
                        ".go", ""
                    ) not in test_file_parser.get_file_name().replace(".go", ""):
                        continue
                    for test_call_method, method_entity in match_same_contain_method(
                        test_file_parser, file_parser
                    ):
                        if method_entity in match_result.keys():
                            match_result[method_entity].append(test_call_method)
                        else:
                            match_result[method_entity] = [test_call_method]
        for file_entity in file_parsers:
            if not file_entity:
                continue
            file_entity.clear_index()
        return match_result
    except Exception as e:
        print(f"-->match error: {type(e).__name__}: {e}")
