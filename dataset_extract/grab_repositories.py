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
import json

from dataset_extract.utils.repo_utils import download_git_repo, extract_repo
from dataset_extract.utils.repo_dependency_utils import  get_repo_dependency

tokens = []

# 初始化全局变量
token_index = 0
remaining_points = 0
last_request_time = datetime.now()
failed_tokens = set()  # 记录遇到 403 错误的 token


def get_remaining_points(headers):
    global remaining_points, last_request_time
    remaining_points = int(headers.get('X-RateLimit-Remaining', 0))
    reset_time = int(headers.get('X-RateLimit-Reset', datetime.now().timestamp()))
    last_request_time = datetime.now() if remaining_points == 0 else datetime.fromtimestamp(reset_time)


def get_token():
    global token_index
    token_index = (token_index + 1) % len(tokens)
    if tokens == []:
        return None
    return tokens[token_index]


def make_request(url):
    global last_request_time, failed_tokens
    max_retry = 5
    while max_retry > 0:
        try:
            headers = {
                'Authorization': f'token {get_token()}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            break
        except Exception as e:
            max_retry -= 1
            print(f"--->Error: Failed to make request to {url}: {e}")
            sleep(10)
    get_remaining_points(response.headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        print(f"--->Error: Received 403 error. Retrying with new token...")
        failed_tokens.add(headers['Authorization'].split()[1])
        if len(failed_tokens) == len(tokens):
            sleep_time = min((last_request_time - datetime.now()).seconds + 1 for _ in tokens)
            print(f"--->Error: All tokens encountered 403 errors. Waiting until {last_request_time}")
            sleep(sleep_time)
            failed_tokens.clear()
        return make_request(url)
    else:
        print(f"--->Error: Failed to make request to {url}: {response.status_code}")
        return None


def make_rest_request(url):
    global last_request_time, failed_tokens
    max_retry = 5
    while True:
        try:
            headers = {
                'Authorization': f'token {get_token()}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            break
        except Exception as e:
            max_retry -= 1
            print(f"--->Error: Failed to make request to {url}: {e}")
            sleep(10)
    get_remaining_points(response.headers)
    if response.status_code == 200:
        if 'next' in response.links:
            next_url = response.links['next']['url']
            next_response = make_rest_request(next_url)
            if next_response:
                return response.json()['items'] + (next_response)
            return response.json()['items']
        return response.json()['items']
    elif response.status_code == 403:
        print(f"--->Error: Received 403 error. Retrying with new token...")
        failed_tokens.add(headers['Authorization'].split()[1])
        if len(failed_tokens) == len(tokens):
            sleep_time = min((last_request_time - datetime.now()).seconds + 1 for _ in tokens)
            print(f"--->Error: All tokens encountered 403 errors. Waiting until {last_request_time}")
            sleep(sleep_time)
            failed_tokens.clear()
        return make_rest_request(url)
    else:
        print(f"--->Error: Failed to make request to {url}: {response.status_code}")
        return None


def make_graphql_request(query, variables):
    global last_request_time, failed_tokens
    data = {'query': query, 'variables': variables}
    max_retry = 5
    while True:
        try:
            headers = {
                'Authorization': f'token {get_token()}',
                'Accept': 'application/json'
            }
            response = requests.post('https://api.github.com/graphql', json=data, headers=headers, timeout=10)
            break
        except Exception as e:
            max_retry -= 1
            print(f"--->Error: Failed to make request to GraphQL API: {e}")
            sleep(10)
    get_remaining_points(response.headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        print(f"--->Error: Received 403 error. Retrying with new token...")
        failed_tokens.add(headers['Authorization'].split()[1]) 
        if len(failed_tokens) == len(tokens):  
            sleep_time = min((last_request_time - datetime.now()).seconds + 1 for _ in tokens) 
            print(f"--->Error: All tokens encountered 403 errors. Waiting until {last_request_time}")
            sleep(sleep_time)
            failed_tokens.clear()  
        return make_graphql_request(query, variables)
    else:
        print(f"--->Error: Failed to make request to GraphQL API: {response.status_code}")
        return None


def search_projects(language, max_results=60000):
    # graphql_query = """
    # query search($query: String!, $maxResults: Int!, $cursor: String) {
    #   search(query: $query, type: REPOSITORY, first: $maxResults, after: $cursor) {
    #     pageInfo {
    #       hasNextPage
    #       endCursor
    #     }
    #     edges {
    #       node {
    #         ... on Repository {
    #           name
    #           url
    #           stargazers {
    #             totalCount
    #           }
    #         }
    #       }
    #     }
    #   }
    # }
    # """
    # variables = {
    #     "query": f"{query} language:{language}",
    #     "maxResults": 100,
    #     "cursor": None
    # }
    # while True:
    #     response_data = make_graphql_request(graphql_query, variables)
    #     if response_data:
    #         projects = [edge['node'] for edge in response_data['data']['search']['edges']]
    #         all_projects.extend(projects)
    #         if len(all_projects) >= max_results or not response_data['data']['search']['pageInfo']['hasNextPage']:
    #             break
    #         variables['cursor'] = response_data['data']['search']['pageInfo']['endCursor']
    #     else:
    #         break
    all_projects = []
    base_url = 'https://api.github.com/search/repositories?q=language:{}+stars:{}..{}&sort=stars&order=desc&per_page=100&page=1'
    mi = 5900
    ma = 310000
    while True:
        url = base_url.format(language, mi-max(ma//100,1), ma)
        test_response = make_request(url)
        if test_response:
            if test_response['total_count'] > 1000:
                print(f"===>Test: Found {test_response['total_count']} projects with url {url}")
                url = base_url.format(language, mi, ma)
                response_data = make_rest_request(url)
                if response_data:
                    print(f"===>Correct: Found {len(response_data)} projects with url {url}")
                    all_projects.extend(response_data)
                    if len(all_projects) >= max_results:
                        break
                    ma = response_data[-1]['stargazers_count']
                    mi = ma - max(ma//100,1)
                else:
                    break
            mi -= max(ma//100,1)
        else:
            break
    return all_projects


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
        print(f"--->Error: Project {repo} does not depend on any of the specified dependencies or SBOM is not available") 
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
            try:
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
            except UnicodeDecodeError as e:
                print(f"--->Error: Failed to decode file {requirements_path}: {e}")
            except Exception as e:
                print(f"--->Error: Failed to parse file {requirements_path}: {e}")
        for ad in all_dependencies:
            if ad is None:
                continue
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

    file_path = os.path.join(xls_path, f"repositories_{language}.json")
    if not os.path.exists(file_path):
        projects = search_projects(language)
        with open(file_path, 'w') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
    else:
        with open(file_path, 'r') as f:
            projects = json.load(f)
    print(f"===>Correct: Found {len(projects)} projects with language {language}")

    idx = 0
    
    for project in projects:
        if project.get('private', False):
            print("--->Error: Private repos not supported. Skipping.")
            continue
        git_group = project['owner']['login']
        git_name = project['name']
        version = project.get('default_branch', '')
        file_name = f"{git_name}-{version.replace('/','-')}.zip"
        download_url = f"https://codeload.github.com/{git_group}/{git_name}/zip/{version}"

        download_path = os.path.join(repo_path, file_name)
        if not os.path.exists(download_path[:-4]):
            if not os.path.exists(download_path):
                download_git_repo(download_url, repo_path, file_name)
            extract_repo(repo_path, file_name)

        if not os.path.exists(download_path[:-4]):
            print(f"===>Error: Failed to download project from {download_url}")
            if os.path.exists(download_path):
                os.remove(download_path)
            continue
        if (parse_dependencies(download_path[:-4], language, specified_dependencies) or
            parse_sbom_dependencies(git_group, git_name, specified_dependencies)):
            print(f"===>Correct: Found {idx}th project {project['name']}")
            update_time = project['updated_at']
            create_time = project['created_at']

            df.loc[idx] = [idx, git_group, git_name, language, version, download_url, file_name, update_time, create_time]
            idx += 1
        else:
            try:
                shutil.rmtree(download_path[:-4])
            except Exception as e:
                print(f"===>Error: Failed to clean up project files: {e}")
        if os.path.exists(download_path):
            os.remove(download_path)

    file_path = os.path.join(xls_path, f"repositories_{language}_1.xlsx")
    df.to_excel(file_path, index=False)
    print(f"===>Correct: Data saved to {file_path}")


def resolve_dependencies(properties):
    xls_path = os.path.abspath(properties["xls_path"])
    old_df = get_repo_dependency(xls_path)
    new_df = pd.DataFrame(columns=['id', 'git_group', 'git_name', 'language', 'version', 'download_url', 'file_name', 'update_time', 'create_time'])
    base_url = "https://api.github.com/repos/{}/{}"
    idx = 0
    for _ , row in old_df.iterrows():
        git_group = row['git_group']
        git_name = row['git_name']
        if 'update_time' not in row or 'create_time' not in row:
            url = base_url.format(git_group, git_name)
            response_data = make_request(url)
            if not response_data:
                print(f"===>Error: Failed to fetch data from {url}")
                continue
            print(f"===>Correct: {idx} Fetched data from {url}")
            create_time = response_data['created_at']
            update_time = response_data['updated_at']
        else :
            create_time = row['create_time']
            update_time = row['update_time']
        idx += 1
        new_df.loc[idx] = [idx, git_group, git_name, row['language'], row['version'], row['download_url'], row['file_name'], update_time, create_time]
    file_path = os.path.join(xls_path, f"repositories_{properties['language']}.xlsx")
    new_df.to_excel(file_path, index=False)
    print(f"===>Correct: Data saved to {file_path}")
        