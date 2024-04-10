#main.py
import sys
import yaml
import os
import shutil

from dataset_extract.repo_api_count_analysis import repo_api_count_analysis
from dataset_extract.top_api_analysis import top_api_analysis


def read_profile():
    try :
        args = sys.argv
        if len(args) >= 2:
            profile = args[1]
        else:
            profile = "./setup/profile.yaml"
        with open(profile) as f:
            properties = yaml.load(f, Loader=yaml.FullLoader)
            return properties
    except Exception as e:
        print(e)
        sys.exit(1)


def init_path(properties):
    if not os.path.exists(properties["repo_path"]):
        os.makedirs(properties["repo_path"])
    if not os.path.exists(properties["csv_path"]):
        os.makedirs(properties["csv_path"])
    if not os.path.exists(properties["json_path"]):
        os.makedirs(properties["json_path"])


def remove_intermediate_files(properties):
    if properties["remove_repo"]:
        if os.path.exists(properties["repo_path"]):
            shutil.rmtree(properties["repo_path"])
    if properties["remove_csv"]:
        if os.path.exists(properties["csv_path"]):
            shutil.rmtree(properties["csv_path"])


def main():
    properties = read_profile()
    language = properties["language"]
    if language != "Java" and language != "Python":
        print("Invalid language")
        sys.exit(1)
    else:
        init_path(properties)
        # repo_api_count_analysis(properties)
        top_api_analysis(properties)
        if properties["remove_repo"]:
            print("Removing repo")
            import shutil
            shutil.rmtree(properties["repo_path"])


if __name__ == "__main__":
    main()