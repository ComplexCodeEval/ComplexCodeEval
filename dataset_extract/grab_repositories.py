import requests
import os
import shutil
from requirements import parse as req_parse
from setuptools.config import setupcfg
from pipfile import Pipfile
import toml
import pandas as pd
from datetime import datetime
from time import sleep
from xml.etree import ElementTree as ET

from dataset_extract.utils.repo_utils import download_git_repo, extract_repo


def make_request(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        print("--->Error: Received 403 error. Waiting before retrying...")
        if 'retry-after' in response.headers:
            retry_after = int(response.headers['retry-after'])
            sleep(retry_after)
        else:
            reset_time = int(response.headers['x-ratelimit-reset'])
            sleep_time = max(reset_time - datetime.now().timestamp(), 60)
            sleep(sleep_time)
        return make_request(url)
    else:
        print(f"--->Error: Failed to make request to {url}: {response.status_code}")
        return None


def search_projects(query, language):
    url = f'https://api.github.com/search/repositories?q={query}+language:{language}'
    return make_request(url)


def parse_requirements_txt(project_name, requirements_content):
    try:
        requirements = req_parse(requirements_content)
        return [req.name for req in requirements]
    except Exception as e:
        return []


def parse_setup_py(project_name, setup_content):
    try:
        config = read_configuration(setup_content)
        install_requires = config['options']['install_requires']
        return install_requires
    except Exception as e:
        return []


def parse_pipfile(project_name, pipfile_content):
    try:
        pipfile = Pipfile.load(pipfile_content)
        return [package for package in pipfile.data['packages']]
    except Exception as e:
        return []


def parse_pyproject_toml(project_name, pyproject_content):
    try:
        pyproject = toml.loads(pyproject_content)
        dependencies = []
        if 'tool' in pyproject and 'poetry' in pyproject['tool'] and 'dependencies' in pyproject['tool']['poetry']:
            dependencies = [dependency.split()[0] for dependency in pyproject['tool']['poetry']['dependencies'].keys()]
        return dependencies
    except Exception as e:
        return []


def parse_pom_xml(project_name, pom_content):
    try:
        dependencies = []
        root = ET.fromstring(pom_content)
        for dependency in root.findall('.//dependency'):
            groupId = dependency.find('groupId').text.strip()
            artifactId = dependency.find('artifactId').text.strip()
            version = dependency.find('version').text.strip()
            dependencies.append(f"{groupId}:{artifactId}:{version}")
        return dependencies
    except Exception as e:
        return []


def find_requirements_path(repo_path, language):
    possible_files = {
        'Python': ['requirements.txt', 'setup.py', 'Pipfile', 'pyproject.toml'],
        'Java': ['pom.xml']
    }
    requirements_paths = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if language == 'python' and file.startswith('requirements') and file.endswith('.txt'):
                requirements_paths.append(os.path.join(root, file))
            elif file in possible_files[language]:
                requirements_paths.append(os.path.join(root, file))
    return requirements_paths


def parse_sbom_dependencies(owner, repo, specified_dependencies):
    sbom_url = f"https://api.github.com/repos/{owner}/{repo}/dependency-graph/sbom"
    return False
    try:
        sbom_data = make_request(sbom_url)
        if sbom_data:
            dependencies = sbom_data['sbom']['packages']
            for dependency in dependencies:
                name = dependency['name']
                if name.startswith('pip:'):
                    for db in specified_dependencies:
                        if db in name.replace('pip:', '', 1).lower():
                            print(f"===>Correct: Project {repo} depends on one of the specified dependencies: {db}")
                            return True
                elif name.startswith('maven:'):
                    for db in specified_dependencies:
                        if db in name.replace('maven:', '', 1).lower():
                            print(f"===>Correct: Project {repo} depends on one of the specified dependencies: {db}")
                            return True  
        print(f"--->Error: Project {repo} does not depend on any of the specified dependencies") 
        return False 
    except Exception as e:
        print(f"--->Error: Failed to fetch SBOM dependencies: {e}")
        return False


def parse_dependencies(repo_path, language, specified_dependencies):
    requirements_paths = find_requirements_path(repo_path, language)
    project_name = os.path.basename(repo_path)
    if requirements_paths:
        all_dependencies = set()
        for requirements_path in requirements_paths:
            with open(requirements_path, 'r') as f:
                requirements_content = f.read()
                file_name = os.path.basename(requirements_path)
                if file_name.startswith('requirements') and file_name.endswith('.txt'):
                    dependencies = parse_requirements_txt(project_name, requirements_content)
                elif file_name == 'setup.py':
                    dependencies = parse_setup_py(project_name, requirements_content)
                elif file_name == 'Pipfile':
                    dependencies = parse_pipfile(project_name, requirements_content)
                elif file_name == 'pyproject.toml':
                    dependencies = parse_pyproject_toml(project_name, requirements_content)
                elif file_name == 'pom.xml':
                    dependencies = parse_pom_xml(project_name, requirements_content)
                all_dependencies.update(dependencies)
        for ad in all_dependencies:
            for db in specified_dependencies:
                if db in ad:
                    print(f"===>Correct: Project {project_name} depends on one of the specified dependencies: {db}")
                    return True
        print(f"--->Error: Project {project_name} does not depend on any of the specified dependencies")
        return False
    else:
        print(f"--->Error: No requirements file found in project {project_name}")
        return False


def grab_repositories(properties):
    repo_path = os.path.abspath(properties["repo_path"])
    xls_path = os.path.abspath(properties["xls_path"])
    language = properties["language"]
    specified_dependencies = []
    for dependency in properties["API"]:
        specified_dependencies.append(dependency["name"].lower())

    df = pd.DataFrame(columns=['id', 'git_group', 'git_name', 'language', 'version', 'download_url', 'file_name', 'update_time', 'create_time'])
    idx = 0

    query = f'stars:>50000'
    projects = search_projects(query, language)['items']

    for project in projects:
        if project.get('private', False):
            print("--->Error: Private repos not supported. Skipping.")
            continue
        git_group = project['owner']['login']
        git_name = project['name']
        version = project.get('default_branch', '')
        file_name = f"{git_name}-{version}.zip"
        download_url = f"https://codeload.github.com/{git_group}/{git_name}/zip/{version}"

        download_path = os.path.join(repo_path, file_name)
        if not os.path.exists(download_path[:-4]):
            if not os.path.exists(download_path):
                download_git_repo(download_url, repo_path, file_name)
            extract_repo(repo_path, file_name)

        if not os.path.exists(download_path[:-4]):
            print(f"===>Error: Failed to download project from {download_url}")
            os.remove(download_path)
            continue

        if (parse_dependencies(download_path[:-4], language, specified_dependencies) or
            parse_sbom_dependencies(git_group, git_name, specified_dependencies)):
            update_time = project['updated_at']
            create_time = project['created_at']

            df.loc[idx] = [idx, git_group, git_name, language, version, download_url, file_name, update_time, create_time]
            idx += 1
        else:
            os.remove(download_path)
            shutil.rmtree(download_path[:-4])

    file_path = os.path.join(xls_path, f"repositories_{language}.xlsx")
    df.to_excel(file_path, index=False)
    print(f"===>Correct: Data saved to {file_path}")
