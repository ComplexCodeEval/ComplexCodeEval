import os
import json
import yaml


def resolve_data(properties):
    json_path = properties["json_path"]
    json_files = []
    for file in os.listdir(json_path):
        if (
            file.endswith(".json")
            and file != properties["language"].lower() + "_results.json"
        ):
            file_path = json_path + "/" + file
            json_files.append(file_path)
    data = {}
    for json_file in json_files:
        with open(json_file, "r") as f:
            data.update(json.load(f))
    results = []
    for key, value in data.items():
        for v in value:
            v["function_update_time"] = v["method_update_time"]
            del v["method_update_time"]
            flag = True
            for index, result in enumerate(results):
                if v["solution"] == result["solution"]:
                    if (
                        v["project_create_time"] > result["project_create_time"]
                        or v["project_update_time"] > result["project_update_time"]
                        or v["file_create_time"] > result["file_create_time"]
                        or v["file_update_time"] > result["file_update_time"]
                    ):
                        v["reference_api"] = result["reference_api"]
                        if key not in v["reference_api"]:
                            v["reference_api"].append(key)
                        results[index] = v
                    else:
                        if key not in results[index]["reference_api"]:
                            results[index]["reference_api"].append(key)
                    flag = False
                    break
            if flag:
                v["reference_api"] = [key]
                results.append(v)
    result_path = os.path.join(
        json_path, properties["language"].lower() + "_results.json"
    )
    with open(result_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


def get_project_parser(project_path, properties):
    try:
        if properties["language"] == "Java":
            from dataset_extract.utils.parse_java import parse_java_file

            java_files = get_java_files(project_path)
            file_parsers = []
            for file in java_files:
                file_parsers.append(parse_java_file(file))
            return file_parsers
        elif properties["language"] == "Python":
            from dataset_extract.utils.parse_python import parse_python_file

            python_files = get_python_files(project_path)
            file_parsers = []
            for file in python_files:
                file_parsers.append(parse_python_file(file))
            return file_parsers
        elif properties["language"] == "Go":
            from dataset_extract.utils.parse_go import parse_go_file

            go_files = get_go_files(project_path)
            file_parsers = []
            for file in go_files:
                file_parsers.append(parse_go_file(file))
            return file_parsers
        else:
            raise Exception("Unsupported language")
    except UnicodeDecodeError:
        return None


from dataset_extract.utils.test_method_extract import match_methods_and_tests
from dataset_extract.utils.test_python_extract import match_functions_and_tests
from dataset_extract.utils.test_go_extract import match_go_methods_and_tests

from dataset_extract.utils.file_utils import (
    get_java_files,
    get_python_files,
    get_go_files,
)


def resolve_java(match_result, root_path, item):
    global count
    del item["test_function"]
    item["test_function"] = []
    for method_entity in match_result.keys():
        class_entity = method_entity.get_belong_class()
        file_entity = class_entity.get_belong_file()
        file_path = file_entity.get_file_path().replace(root_path, "")
        if file_path == item["file_path"]:
            if class_entity.get_class_name() == item["focal_class"]:
                if method_entity.get_method_name() == item["focal_name"]:
                    for test_method in match_result[method_entity]:
                        test_file = test_method.get_belong_class().get_belong_file()
                        test_file_path = test_file.get_file_path().replace(
                            root_path, ""
                        )
                        test_package = test_file.get_package_text().replace(".", "/")
                        item["test_function"].append(
                            {
                                "file_path": test_file_path,
                                "package": test_package,
                                "class_name": test_method.get_belong_class().get_class_name(),
                                "method_name": test_method.get_method_name(),
                                "code": test_method.get_code(),
                            }
                        )
                    count += 1
                    print(count)
                    break


def resolve_python(match_result, root_path, item):
    del item["test_function"]
    global count
    item["test_function"] = []
    for function_entity in match_result.keys():
        file_entity = function_entity.get_belong_file()
        file_path = file_entity.get_file_path().replace(root_path, "")
        if file_path == item["file_path"]:
            if function_entity.get_function_name() == item["focal_name"]:
                for test_function in match_result[function_entity]:
                    test_file = test_function.get_belong_file()
                    test_file_path = test_file.get_file_path().replace(root_path, "")
                    if test_class := test_function.get_belong_class():
                        class_name = test_class.get_class_name()
                    else:
                        class_name = None
                    item["test_function"].append(
                        {
                            "file_path": test_file_path,
                            "class_name": class_name,
                            "function_name": test_function.get_function_name(),
                            "code": test_function.get_code(),
                        }
                    )
                count += 1
                print(count)
                break


def resolve_go(match_result, root_path, item):
    del item["test_functions"]
    global count
    item["test_function"] = []
    for method_entity in match_result.keys():
        file_entity = method_entity.get_belong_file()
        file_path = file_entity.get_file_path().replace(root_path, "")
        if file_path == item["file_path"]:
            if method_entity.get_function_name() == item["focal_name"]:
                for test_method in match_result[method_entity]:
                    test_file = test_method.get_belong_file()
                    test_file_path = test_file.get_file_path().replace(root_path, "")
                    item["test_function"].append(
                        {
                            "file_path": test_file_path,
                            "function_name": test_method.get_function_name(),
                            "code": test_method.get_code(),
                        }
                    )
                item["solution"] = method_entity.get_code()
                item["left_context"] = method_entity.get_left_context()
                item["right_context"] = method_entity.get_right_context()
                count += 1
                print(count)
                break


def resolve_code(properties):
    if properties["language"] == "Go":
        file_path = os.path.join(
            properties["json_path"], properties["language"].lower() + "_results.json"
        )
    elif properties["language"] == "Python":
        file_path = "/data/jiachen/java_api/dataset_extract/backup/results/json_results/python_results.json"
    elif properties["language"] == "Java":
        file_path = "/data/jiachen/java_api/dataset_extract/backup/results/json_results/java_results.json"
    else:
        raise Exception("Unsupported language")
    root_path = properties["repo_path"]
    root_path = os.path.abspath(root_path)
    data = []
    with open(file_path, "r") as f:
        data = json.load(f)
    results = []
    for item in data:
        project_path = root_path + "/" + item["project_name"].replace(".zip", "")
        file_parsers = get_project_parser(project_path, properties)
        if properties["language"] == "Java":
            match_result = match_methods_and_tests(file_parsers)
            resolve_java(match_result, root_path, item)
        elif properties["language"] == "Python":
            match_result = match_functions_and_tests(file_parsers)
            resolve_python(match_result, root_path, item)
        elif properties["language"] == "Go":
            match_result = match_go_methods_and_tests(file_parsers)
            resolve_go(match_result, root_path, item)
        results.append(item)
    with open("./ComplexCodeEval-" + properties["language"] + ".json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


def resolve_prompt(properties):
    from dataset_extract.utils.comment_gen_utils import gen_comment_from_api

    global count
    with open("./ComplexCodeEval-" + properties["language"] + ".json", "r") as f:
        data = json.load(f)
    result_path = "./ComplexCodeEval-" + properties["language"] + "_new.json"
    with open(result_path, "r") as f:
        results = json.load(f)
    item = data[294]
    item["prompt"] = gen_comment_from_api(
        item["solution"], item["reference_api"][0], properties["language"]
    )
    results.append(item)
    with open(result_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    # for item in data:
    #     if item['prompt'] == None:
    #         try:
    #             item['prompt'] = gen_comment_from_api(item['solution'], item['reference_api'][0], properties['language'])
    #             count += 1
    #             print(count)
    #             with open(result_path, 'a') as f:
    #                 json.dump(item, f, ensure_ascii=False, indent=4)
    #         except Exception as e:
    #             print(e)
    #             print('--->Error: gen comment from api failed')


def resolve_dependencies(properties):
    with open("./ComplexCodeEval-" + properties["language"] + "_new.json", "r") as f:
        data = json.load(f)
    for item in data:
        dependencies = item["function_dependencies"]
        # 去重
        dependencies = list(set(dependencies))
        item["function_dependencies"] = dependencies
    with open("./ComplexCodeEval-" + properties["language"] + "_new.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


count = 0

if __name__ == "__main__":
    profile = "/data/jiachen/java_api/dataset_extract/setup/profile.yaml"
    with open(profile) as f:
        properties = yaml.load(f, Loader=yaml.FullLoader)
    # resolve_data(properties)
    resolve_code(properties)
