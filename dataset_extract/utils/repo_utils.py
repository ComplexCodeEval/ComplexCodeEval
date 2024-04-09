#下载和解压缩项目的相关工具

import requests
import os
import zipfile


def download_git_repo(download_url, repo_path, file_name, retry = 0):
    try:
        response = requests.get(download_url)
        with open(os.path.join(repo_path, file_name), 'wb') as f:
            f.write(response.content)
    except requests.exceptions.SSLError:
        # retry
        if retry < 10:
            print(f"Retry {retry} times")
            download_git_repo(download_url, file_name, retry + 1)
        else:
            exit(1)
        # download_git_repo(download_url, git_name, file_name, retry + 1)


def extract_repo(repo_path, file_name):
    file_path = os.path.join(repo_path, file_name)
    extract_path = os.path.join(repo_path, file_name)[:-4]
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    except zipfile.BadZipFile:
        print(f"BadZipFile: {file_path}, skip this file")