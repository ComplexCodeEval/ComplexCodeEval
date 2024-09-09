# 下载和解压缩项目的相关工具

import requests
import os
import zipfile
import urllib.parse


def download_git_repo(download_url, repo_path, file_name, retry=0, timeout=120):
    try:
        download_url = urllib.parse.quote(download_url, safe=":/")
        with requests.get(download_url, stream=True, timeout=timeout) as response:
            response.raise_for_status()  # 检查响应状态码
            with open(os.path.join(repo_path, file_name), "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        return
    except requests.exceptions.Timeout:
        print("--->Error: Request timed out.")
    except requests.exceptions.SSLError:
        print("--->Error: SSL certificate error.")
    except requests.exceptions.RequestException as e:
        print(
            f"--->Error: An error occurred during the request: {e} with {download_url}"
        )
    # 重试
    if retry < 10:
        print(f"--->Test: Retry {retry} times with {download_url}")
        download_git_repo(download_url, repo_path, file_name, retry + 1, timeout + 20)
    else:
        print("--->Error: Max retries exceeded. Exiting.")


def extract_repo(repo_path, file_name):
    file_path = os.path.join(repo_path, file_name)
    if not os.path.exists(file_path):
        print(f"--->Error: File not found: {file_path}")
        return
    extract_path = os.path.join(repo_path, file_name)[:-4]
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
    except zipfile.BadZipFile:
        print(f"--->Error: BadZipFile: {file_path}, skip this file")
    except OSError as e:
        print(f"--->Error: {e}")
