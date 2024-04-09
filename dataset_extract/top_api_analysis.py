# 分析调用api的method，得到java数据集

import pandas as pd
import os
import json

from dataset_extract.utils.repo_utils import download_git_repo, extract_repo
from dataset_extract.utils.file_utils import get_java_files, get_python_files
from dataset_extract.utils.parse import parse_java_file, parse_python_file
from dataset_extract.utils.test_method_extract import match_methods_and_tests
from dataset_extract.utils.test_python_extract import match_functions_and_tests
from dataset_extract.Entity.result_entity import resultEntity
from dataset_extract.Entity.python_result_entity import pythonResultEnity
from dataset_extract.utils.comment_gen_utils import gen_comment_from_api
from dataset_extract.utils.deduplicate import analysis_result
from dataset_extract.utils.repo_dependency_utils import get_repo_dependency


def java_result_gen(match_result, api, count_api, api_json, xls_df, git_name, project_name, repo_path):
    flag = False
    for method_entity in match_result.keys():
        file_entity = method_entity.get_belong_class().get_belong_file()
        class_entity = method_entity.get_belong_class()
        import_texts = file_entity.get_import_text()
        package_text = file_entity.get_package_text()
        for invocation_method in method_entity.get_call_method():
            if invocation_method.get_call_method_name() not in api:
                continue
            for import_text in import_texts:
                if import_text in api:
                    temp = ".".join(import_text.split(".")[:-1])
                    temp = temp + "." + invocation_method.get_call_method_name()
                    if temp == api:
                        result_entity = resultEntity()
                        print(
                            f"===>Correct: find {count_api}th api {len(api_json) + 1}th method "
                            f": {api} in {method_entity.get_method_name()}")
                        temp_df = xls_df[
                            (xls_df['git_name'] == git_name) & (xls_df['file_name'] == project_name + ".zip")]
                        result_entity.set_git_group(temp_df["git_group"].values[0])
                        result_entity.set_git_name(git_name)
                        result_entity.set_language(temp_df["language"].values[0])
                        result_entity.set_version(temp_df["version"].values[0])
                        result_entity.set_project_name(project_name + ".zip")
                        try:
                            result_entity.set_create_time(temp_df["create_time"].values[0].isoformat())
                        except:
                            pass
                        result_entity.set_update_time(temp_df["update_time"].values[0].isoformat())
                        result_entity.set_file_path(file_entity.get_file_path().replace(repo_path, ""))
                        file_path = result_entity.get_file_path()
                        temp_path = "".join(file_path.split(project_name + "/")[-1]).split("/src/main")
                        # package_path = temp_path[-1]
                        if len(temp_path) > 1 and temp_path[0] != "":
                            module_path = temp_path[0]
                        else:
                            module_path = project_name
                        result_entity.set_focal_module(module_path)
                        result_entity.set_focal_package(package_text.replace(".", "/"))
                        result_entity.set_focal_class(class_entity.get_class_name())
                        result_entity.set_focal_name(method_entity.get_method_name())
                        for parameter_entity in method_entity.get_parameter_entity():
                            result_entity.set_focal_parameter(parameter_entity.get_parameter_type())
                        result_entity.set_solution(method_entity.get_node().text.decode("utf-8"))
                        result_entity.set_method_signature(method_entity.get_method_signature())
                        result_entity.set_left_context(method_entity.get_left_context())
                        result_entity.set_right_context(method_entity.get_right_context())
                        for test_method in match_result[method_entity]:
                            result_entity.set_test_function(test_method.get_node().text.decode("utf-8"))
                        result_entity.set_class_comment(class_entity.get_comment())
                        for import_text in import_texts:
                            result_entity.set_import_text(import_text)
                        result_entity.set_prompt(method_entity.get_comment())
                        if not result_entity.get_prompt():
                            result_entity.set_prompt(
                                gen_comment_from_api(result_entity.get_solution(), api, language="java"))
                            result_entity.set_is_gen_from_api()
                        api_json.append(vars(result_entity))
                        flag = True
                        break
            if flag:
                break
        if flag:
            break


def python_result_gen(match_result, api, count_api, api_json, xls_df, git_name, project_name, repo_path):
    flag = False
    for function_entity in match_result.keys():
        file_entity = function_entity.get_belong_file()
        class_entity = function_entity.get_belong_class()
        for call_method in function_entity.get_call_method():
            if api == call_method.get_call_api():
                result_entity = pythonResultEnity()
                print(
                    f"===>Correct: find {count_api}th api {len(api_json) + 1}th method "
                    f": {api} in {function_entity.get_function_name()}")
                temp_df = xls_df[
                    (xls_df['git_name'] == git_name) & (xls_df['file_name'] == project_name + ".zip")]
                result_entity.set_git_group(temp_df["git_group"].values[0])
                result_entity.set_git_name(git_name)
                result_entity.set_language(temp_df["language"].values[0])
                result_entity.set_version(temp_df["version"].values[0])
                result_entity.set_project_name(project_name + ".zip")
                try:
                    result_entity.set_create_time(temp_df["create_time"].values[0].isoformat())
                except:
                    pass
                result_entity.set_update_time(temp_df["update_time"].values[0].isoformat())
                result_entity.set_file_path(file_entity.get_file_path().replace(repo_path, ""))
                result_entity.set_file_name(file_entity.get_file_name())
                if class_entity:
                    result_entity.set_focal_class(class_entity.get_class_name())
                result_entity.set_focal_name(function_entity.get_function_name())
                for parameter_entity in function_entity.get_parameter_entity():
                    result_entity.set_focal_parameter(parameter_entity.get_parameter_name())
                function_node = function_entity.get_node()
                result_entity.set_solution(function_node.text.decode("utf-8"))
                result_entity.set_function_signature(function_entity.get_function_signature())
                result_entity.set_left_context(function_entity.get_left_context())
                result_entity.set_right_context(function_entity.get_right_context())
                for test_function_entity in match_result[function_entity]:
                    result_entity.set_test_function(test_function_entity.get_node().text.decode("utf-8"))
                for import_text in file_entity.get_import_text():
                    result_entity.set_import_text(import_text)
                result_entity.set_prompt(function_entity.get_comment())
                if not result_entity.get_prompt():
                    result_entity.set_prompt(gen_comment_from_api(result_entity.get_solution(), api, language="python"))
                    result_entity.set_is_gen_from_api()
                api_json.append(vars(result_entity))
                flag = True
                break
        if flag:
            break


def get_project_parser(project_path, properties):
    if properties["language"] == "Java":
        java_files = get_java_files(project_path)
        file_parsers = []
        for file in java_files:
            file_parsers.append(parse_java_file(file))
        return file_parsers
    elif properties["language"] == "Python":
        python_files = get_python_files(project_path)
        file_parsers = []
        for file in python_files:
            file_parsers.append(parse_python_file(file))
        return file_parsers
    else:
        raise Exception("Unsupported language")


def analysis_top_api(properties, api_count_path, api_count_analysis_path, comment_tested_API_1, comment_tested_API_2):
    xls_path = os.path.abspath(properties["xls_path"])
    repo_path = os.path.abspath(properties["repo_path"])

    api_count_csv_df = pd.read_csv(api_count_path)
    api_count_analysis_csv_df = pd.read_csv(api_count_analysis_path)
    xls_df = get_repo_dependency(xls_path)
    api_count_csv_df = api_count_csv_df.drop(columns=['count']).drop_duplicates()

    count_api = 1
    count = 0
    json_result = {}
    json_result_api = {}
    json_result_method = {}

    for api in api_count_analysis_csv_df['api'].values:
        print(f"*****Processing {count_api}th api: {api}*****")
        api_json = []
        for index, row in api_count_csv_df[api_count_csv_df["api"] == api].iterrows():
            project_name = row['project_name']
            git_name = row['git_name']
            project_path = os.path.join(repo_path, project_name)
            if not os.path.exists(project_path):
                if not os.path.exists(project_path + ".zip"):
                    download_url_df = \
                        xls_df[(xls_df['git_name'] == git_name) & (xls_df['file_name'] == project_name + ".zip")][
                            'download_url']
                    if not download_url_df.empty:
                        download_url = download_url_df.values[0]
                        download_git_repo(download_url, repo_path, project_name + ".zip")
                        extract_repo(repo_path, project_name + ".zip")
            if not os.path.exists(project_path):
                os.remove(project_path + ".zip")
                continue
            file_parsers = get_project_parser(project_path, properties)
            if not file_parsers:
                print(f"--->project {project_name} has no java files")
                continue
            if properties["language"] == "Java":
                match_result = match_methods_and_tests(file_parsers)
                if not match_result:
                    print(f"--->Error: project {project_name} has no match result")
                    continue
                java_result_gen(match_result, api, count_api, api_json, xls_df, git_name, project_name, repo_path)
            elif properties["language"] == "Python":
                match_result = match_functions_and_tests(file_parsers)
                if not match_result:
                    print(f"--->Error: project {project_name} has no match result")
                    continue
                python_result_gen(match_result, api, count_api, api_json, xls_df, git_name, project_name, repo_path)
            else:
                raise Exception("Unsupported language")
            if len(api_json) == 10:
                break
        if len(api_json) > 0:
            count_api += 1
            json_result[api] = api_json
            if count < 100:
                json_result_api[api] = api_json
                count += 1
            if count == 100:
                count = analysis_result(json_result_api)
                if count == 100:
                    break
    analysis_result(json_result_api)
    # total_count = analysis_result(json_result)
    # print(f"===>Done: {total_count} sets of APIs that meet the requirements")
    # if total_count > 100:
    #     for i in range(100):
    #         m = (0, None)
    #         for key in json_result.keys():
    #             if key not in json_result_method.keys():
    #                 if len(json_result[key]) > m[0]:
    #                     m = (len(json_result[key]), key)
    #         if m[1]:
    #             json_result_method[m[1]] = json_result[m[1]]
    # else :
    #     json_result_method = json_result
    with open(comment_tested_API_1, 'w') as f:
        json.dump(json_result_api, f, indent=2)
    # with open(current_path + json_path + comment_tested_API_2, 'w') as f:
    #     json.dump(json_result_method, f, indent=2)


def top_api_analysis(properties):
    csv_path = os.path.abspath(properties["csv_path"])
    json_path = os.path.abspath(properties["json_path"])
    for api in properties['API']:
        api_count_name = f"{properties['language']}_{api['name']}_repo_api_count.csv"
        api_count_analysis_name = f"{properties['language']}_{api['name']}_repo_api_count_analysis.csv"
        comment_tested_API_1 = f"{properties['language']}_{api['name']}_comment_tested_API_1.json"
        comment_tested_API_2 = f"{properties['language']}_{api['name']}_comment_tested_API_2.json"
        api_count_path = os.path.join(csv_path, api_count_name)
        api_count_analysis_path = os.path.join(csv_path, api_count_analysis_name)
        comment_tested_API_1_path = os.path.join(json_path, comment_tested_API_1)
        comment_tested_API_2_path = os.path.join(json_path, comment_tested_API_2)
        analysis_top_api(properties, api_count_path, api_count_analysis_path, comment_tested_API_1_path,
                         comment_tested_API_2_path)
