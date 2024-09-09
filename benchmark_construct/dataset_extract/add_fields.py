import os
import re
import json

from dataset_extract.utils.request_utils import make_request


API_URL_TEMPLATE_COMMITS = (
    "https://api.github.com/repos/{owner}/{repo}/commits?path={filename}&sha={ref}"
)
API_URL_TEMPLATE_BRANCHES = "https://api.github.com/repos/{owner}/{repo}/branches"


def analyze_diff_for_function_change(sample_function, diff_info):
    cleaned_diff = re.sub(r"@@.*@@", "", diff_info)
    sample_function_lines = [
        line.strip() for line in sample_function.split("\n") if line.strip()
    ]
    diff_lines = [line.strip() for line in cleaned_diff.split("\n") if line.strip()]
    for i, diff_line in enumerate(diff_lines):
        if diff_line.startswith("+"):
            if diff_line[1:] in sample_function_lines:
                return True
        # elif diff_line.startswith('-'):
        #     if i > 0 and diff_lines[i-1] in sample_function_lines:
        #         return True
    return False


def get_file_info(owner, repo, filename, branch, sample_function):
    file_create_time = None
    file_update_time = None
    function_upadte_time = None

    api_url_commits = API_URL_TEMPLATE_COMMITS.format(
        owner=owner, repo=repo, filename=filename, ref=branch
    )
    commits = make_request(api_url_commits)

    if commits:
        file_update_time = commits[0]["commit"]["author"]["date"]
        file_create_time = commits[-1]["commit"]["author"]["date"]
        for commit in commits:
            if function_upadte_time:
                break
            commit_sha = commit["sha"]
            commit_date = commit["commit"]["author"]["date"]

            diff_url = (
                f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            )
            diff_info = make_request(diff_url)

            if diff_info:
                for file_diff in diff_info["files"]:
                    try:
                        if file_diff["filename"] == filename:
                            if analyze_diff_for_function_change(
                                sample_function, file_diff["patch"]
                            ):
                                function_upadte_time = commit_date
                                break
                    except Exception as e:
                        print(
                            f"--->Error: Failed to analyze diff for function change: {e} from url: {diff_url}"
                        )
                        continue

    api_url_branches = API_URL_TEMPLATE_BRANCHES.format(owner=owner, repo=repo)
    branches = make_request(api_url_branches)

    if branches:
        for branch in branches:
            ref = branch["name"]
            api_url_commits = API_URL_TEMPLATE_COMMITS.format(
                owner=owner, repo=repo, filename=filename, ref=ref
            )
            commits = make_request(api_url_commits)

            if commits:
                creation_time = commits[-1]["commit"]["author"]["date"]
                if not file_create_time or creation_time < file_create_time:
                    file_create_time = creation_time

    if not file_update_time:
        file_update_time = file_create_time
    return file_create_time, file_update_time, function_upadte_time


def add_file_time(properties):
    json_file_path = os.path.abspath(properties["json_path"])
    json_files = []
    for file in os.listdir(json_file_path):
        if file.endswith(".json"):
            file_path = json_file_path + "/" + file
            json_files.append(file_path)
    for json_file in json_files:
        with open(json_file, "r") as f:
            print("===>Processing file: ", json_file)
            data = json.load(f)
            for key in data.keys():
                print("===>Processing API: ", key)
                for value in data[key]:
                    try:
                        if "project_create_time" in value.keys():
                            continue
                        print(
                            "===>Processing data: git_group: ",
                            value["git_group"],
                            "git_name: ",
                            value["git_name"],
                            "version ",
                            value["version"],
                        )
                        git_group = value["git_group"]
                        git_name = value["git_name"]
                        version = value["version"]
                        project_create_time = value["create_time"]
                        project_update_time = value["update_time"]
                        file_name = "/".join(value["file_path"].split("/")[3:])
                        solution = value["solution"]
                        file_create_time, file_update_time, function_upadte_time = (
                            get_file_info(
                                git_group, git_name, file_name, version, solution
                            )
                        )
                        del value["create_time"]
                        del value["update_time"]
                        if not file_create_time:
                            file_create_time = project_create_time
                        if not file_update_time:
                            file_update_time = file_create_time
                        if not function_upadte_time:
                            function_upadte_time = file_create_time
                        value["project_create_time"] = project_create_time
                        value["project_update_time"] = project_update_time
                        value["file_create_time"] = file_create_time
                        value["file_update_time"] = file_update_time
                        if value["language"] == "Python" or value["language"] == "Go":
                            value["function_update_time"] = function_upadte_time
                        else:
                            value["method_update_time"] = function_upadte_time
                    except Exception as e:
                        print(f"--->Error: Failed to process data: {e}")
                        continue
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def add_license(properties):
    json_file_path = os.path.abspath(properties["json_path"])
    json_files = []
    for file in os.listdir(json_file_path):
        if file.endswith(".json"):
            file_path = json_file_path + "/" + file
            json_files.append(file_path)
    for json_file in json_files:
        with open(json_file, "r") as f:
            print("===>Processing file: ", json_file)
            data = json.load(f)
            for key in data.keys():
                print("===>Processing API: ", key)
                for value in data[key]:
                    try:
                        if "license" in value.keys():
                            continue
                        print(
                            "===>Processing data: git_group: ",
                            value["git_group"],
                            "git_name: ",
                            value["git_name"],
                            "version ",
                            value["version"],
                        )
                        git_group = value["git_group"]
                        git_name = value["git_name"]
                        api_url = f"https://api.github.com/repos/{git_group}/{git_name}/license"
                        license = make_request(api_url)
                        if license:
                            value["license"] = license["license"]
                        else:
                            value["license"] = None
                    except Exception as e:
                        print(f"--->Error: Failed to process data: {e}")
                        continue
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
