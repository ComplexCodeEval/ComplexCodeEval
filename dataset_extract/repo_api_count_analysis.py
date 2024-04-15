# 通过分析java项目，获取api调用的信息

import csv
import os
from collections import Counter
import pandas as pd

from dataset_extract.utils.repo_utils import download_git_repo, extract_repo
from dataset_extract.utils.file_utils import get_java_files, get_python_files
from dataset_extract.utils.parse import analyze_java_api, analyze_python_api
from dataset_extract.utils.repo_dependency_utils import get_repo_dependency


def analyze_api_count(source_file_path, target_file_path):
    df = pd.read_csv(source_file_path)
    df = df.groupby('api', as_index=False).agg({"count": "sum"})
    df = df.sort_values(by='count', ascending=False)
    df = df[df["count"] > 10]
    df.to_csv(target_file_path, index=False)


def csv_write_row(file_path, data, git_name, project_name):
    with open(file_path, 'a+') as f:
        writer = csv.writer(f)
        for api, api_count in data.items():
            writer.writerow([api, api_count, git_name, project_name])


def csv_init(file_path):
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["api", "count", "git_name", "project_name"])


def get_api(path, properties):
    try :
        language = properties["language"]
        if language == 'Java':
            java_files = get_java_files(path)
            for file in java_files:
                try:
                    yield from analyze_java_api(file, properties["API"]).items()
                except UnicodeDecodeError:
                    raise
                except Exception:
                    continue
        elif language == 'Python':
            python_files = get_python_files(path)
            for file in python_files:
                try:
                    yield from analyze_python_api(file, properties["API"]).items()
                except UnicodeDecodeError:
                    raise
                except Exception:
                    continue
        else:
            raise Exception("Unsupported language")
    except UnicodeDecodeError:
        pass


def repo_api_count_analysis(properties):
    csv_path = os.path.abspath(properties["csv_path"])
    xls_path = os.path.abspath(properties["xls_path"])
    repo_path = os.path.abspath(properties["repo_path"])

    api_count_csv_path = {}
    for api in properties["API"]:
        api_count_name = f"{properties['language']}_{api['name']}_repo_api_count.csv"
        api_count_csv_path[api['name']] = os.path.join(csv_path, api_count_name)
    for _, api_path in api_count_csv_path.items():
        csv_init(api_path)

    xls_df = get_repo_dependency(xls_path)

    count = 1

    for index, row in xls_df.iterrows():
        api_counter = {}
        for api in properties["API"]:
            api_counter[api['name']] = Counter()
        git_name = row['git_name']
        print(f"Processing {count}th repo: {git_name}")
        count += 1
        download_url = row['download_url']
        filename = row['file_name']
        zip_location = os.path.join(repo_path, filename)
        if not os.path.exists(zip_location[:-4]):
            if not os.path.exists(zip_location):
                download_git_repo(download_url, repo_path, filename)
            extract_repo(repo_path, filename)

        if not os.path.exists(zip_location[:-4]):
            os.remove(zip_location)
            continue

        for key, value in get_api(zip_location[:-4], properties):
            api_counter[key].update(value)

        for api_name, api_count in api_counter.items():
            csv_write_row(api_count_csv_path[api_name], api_count, git_name, filename[:-4])

        if os.path.exists(zip_location):
            os.remove(zip_location)

    for _, api_path in api_count_csv_path.items():
        analyze_api_count(api_path, api_path[:-4] + "_analysis.csv")
