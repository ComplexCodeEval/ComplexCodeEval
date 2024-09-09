import os
import shutil
from requirements import parse as req_parse
from pipfile import Pipfile
import toml
import pandas as pd
from xml.etree import ElementTree as ET
import json
from setuptools.config import read_configuration

from dataset_extract.utils.repo_utils import download_git_repo, extract_repo
from dataset_extract.utils.repo_dependency_utils import get_repo_dependency
from dataset_extract.utils.request_utils import make_request, make_rest_request


def search_projects(language, min_stars):
    all_projects = []
    base_url = "https://api.github.com/search/repositories?q=language:{}+stars:{}..{}&sort=stars&order=desc&per_page=100&page=1"
    mi = 5000
    ma = 500000
    while True:
        url = base_url.format(language, mi - max(ma // 100, 1), ma)
        test_response = make_request(url)
        if test_response:
            if test_response["total_count"] > 1000 or mi <= min_stars:
                if mi <= min_stars:
                    url = base_url.format(language, min_stars, ma)
                    response_data = make_rest_request(url)
                    if response_data:
                        print(
                            f"===>Correct: Found {len(response_data)} projects with url {url}"
                        )
                        all_projects.extend(response_data)
                    break
                else:
                    url = base_url.format(language, mi, ma)
                    response_data = make_rest_request(url)
                    if response_data:
                        print(
                            f"===>Correct: Found {len(response_data)} projects with url {url}"
                        )
                        all_projects.extend(response_data)
                        ma = response_data[-1]["stargazers_count"] - 1
                    else:
                        break
            mi -= max(ma // 100, 1)
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
        install_requires = config["options"]["install_requires"]
        return install_requires
    except Exception as e:
        return []


def parse_pipfile(project_name, pipfile_content):
    try:
        pipfile = Pipfile.load(pipfile_content)
        return [package for package in pipfile.data["packages"]]
    except Exception as e:
        return []


def parse_pyproject_toml(project_name, pyproject_content):
    try:
        pyproject = toml.loads(pyproject_content)
        dependencies = []
        if (
            "tool" in pyproject
            and "poetry" in pyproject["tool"]
            and "dependencies" in pyproject["tool"]["poetry"]
        ):
            dependencies = [
                dependency.split()[0]
                for dependency in pyproject["tool"]["poetry"]["dependencies"].keys()
            ]
        return dependencies
    except Exception as e:
        return []


def parse_pom_xml(project_name, pom_content):
    try:
        dependencies = []
        root = ET.fromstring(pom_content)
        ns = {"ns": root.tag.split("}")[0][1:]}  # 提取命名空间
        for dependency in root.findall(".//ns:dependency", ns):
            groupId_element = dependency.find("ns:groupId", ns)
            artifactId_element = dependency.find("ns:artifactId", ns)
            groupId = (
                groupId_element.text.strip() if groupId_element is not None else ""
            )
            artifactId = (
                artifactId_element.text.strip()
                if artifactId_element is not None
                else ""
            )
            if groupId or artifactId:
                dependency = f"{groupId}:{artifactId}"
                dependencies.append(dependency.lower().replace("-", "."))
        return dependencies
    except Exception as e:
        return []


def parse_go_mod(project_name, go_mod_content):
    try:
        dependencies = []
        pattern = re.compile(r"^\s*require\s+([^\s]+)\s+([^\s]+)$", re.MULTILINE)
        matches = pattern.findall(go_mod_content)
        for match in matches:
            dependency = match[0].lower()
            dependencies.append(dependency)
        return dependencies
    except Exception as e:
        return []


def find_requirements_path(repo_path, language):
    possible_files = {
        "Python": ["requirements.txt", "setup.py", "Pipfile", "pyproject.toml"],
        "Java": ["pom.xml"],
        "Go": ["go.mod"],
    }
    requirements_paths = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if (
                language == "python"
                and file.startswith("requirements")
                and file.endswith(".txt")
            ):
                requirements_paths.append(os.path.join(root, file))
            elif file in possible_files[language]:
                requirements_paths.append(os.path.join(root, file))
    return requirements_paths


def parse_sbom_dependencies(owner, repo, specified_dependencies):
    sbom_url = f"https://api.github.com/repos/{owner}/{repo}/dependency-graph/sbom"
    try:
        sbom_data = make_request(sbom_url)
        if sbom_data:
            dependencies = sbom_data["sbom"]["packages"]
            for dependency in dependencies:
                name = dependency["name"]
                if name.startswith("pip:"):
                    for db in specified_dependencies:
                        if db in name.replace("pip:", "", 1).lower():
                            print(
                                f"===>Correct: Project {repo} depends on one of the specified dependencies: {db}"
                            )
                            return True
                elif name.startswith("maven:"):
                    for db in specified_dependencies:
                        if db in name.replace("maven:", "", 1).lower().replace(
                            "-", "."
                        ):
                            print(
                                f"===>Correct: Project {repo} depends on one of the specified dependencies: {db}"
                            )
                            return True
                elif name.startswith("go:"):
                    for db in specified_dependencies:
                        if db in name.replace("go:", "", 1).lower():
                            print(
                                f"===>Correct: Project {repo} depends on one of the specified dependencies: {db}"
                            )
                            return True
        print(
            f"--->Error: Project {repo} does not depend on any of the specified dependencies or SBOM is not available"
        )
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
                with open(requirements_path, "r") as f:
                    requirements_content = f.read()
                    file_name = os.path.basename(requirements_path)
                    if file_name.startswith("requirements") and file_name.endswith(
                        ".txt"
                    ):
                        dependencies = parse_requirements_txt(
                            project_name, requirements_content
                        )
                    elif file_name == "setup.py":
                        dependencies = parse_setup_py(
                            project_name, requirements_content
                        )
                    elif file_name == "Pipfile":
                        dependencies = parse_pipfile(project_name, requirements_content)
                    elif file_name == "pyproject.toml":
                        dependencies = parse_pyproject_toml(
                            project_name, requirements_content
                        )
                    elif file_name == "pom.xml":
                        dependencies = parse_pom_xml(project_name, requirements_content)
                    elif file_name == "go.mod":
                        dependencies = parse_go_mod(project_name, requirements_content)
                    all_dependencies.update(dependencies)
            except UnicodeDecodeError as e:
                print(f"--->Error: Failed to decode file {requirements_path}: {e}")
            except Exception as e:
                print(f"--->Error: Failed to parse file {requirements_path}: {e}")
        for ad in all_dependencies:
            if ad is None:
                continue
            for db in specified_dependencies:
                if db in ad.lower():
                    print(
                        f"===>Correct: Project {project_name} depends on one of the specified dependencies: {db}"
                    )
                    return True
        print(
            f"--->Error: Project {project_name} does not depend on any of the specified dependencies"
        )
        return False
    else:
        print(f"--->Error: No requirements file found in project {project_name}")
        return False


def get_repo_tag(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/tags"
    response_data = make_request(url)
    if response_data:
        return response_data[0]["name"]
    return None


def grab_repositories(properties):
    repo_path = os.path.abspath(properties["repo_path"])
    xls_path = os.path.abspath(properties["xls_path"])
    language = properties["language"]
    specified_dependencies = []
    if language == "Python":
        for dependency in properties["API"]:
            specified_dependencies.append(dependency["name"].lower())
    elif language == "Java":
        for dependency in properties["API"]:
            specified_dependencies.append(
                dependency["name"].lower().replace("_", ".").replace("-", ".")
            )
            for accept in dependency["accept"]:
                specified_dependencies.append(accept.lower())
    elif language == "Go":
        for dependency in properties["API"]:
            specified_dependencies.append(dependency["name"].lower())

    df = pd.DataFrame(
        columns=[
            "id",
            "git_group",
            "git_name",
            "language",
            "version",
            "download_url",
            "file_name",
            "update_time",
            "create_time",
        ]
    )

    file_path = os.path.join(xls_path, f"repositories_{language}.json")
    if not os.path.exists(file_path):
        projects = search_projects(language, properties["min_stars"])
        with open(file_path, "w") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
    else:
        with open(file_path, "r") as f:
            projects = json.load(f)
    print(f"===>Correct: Found {len(projects)} projects with language {language}")

    idx = 0

    for project in projects:
        if project.get("private", False):
            print("--->Error: Private repos not supported. Skipping.")
            continue
        git_group = project["owner"]["login"]
        git_name = project["name"]
        if tag_name := get_repo_tag(git_group, git_name):
            version = tag_name
            download_url = f"https://codeload.github.com/{git_group}/{git_name}/zip/refs/tags/{version}"
        else:
            version = project.get("default_branch", "")
            download_url = f"https://codeload.github.com/{git_group}/{git_name}/zip/refs/heads/{version}"
        file_name = f"{git_name}-{version.replace('/','-')}.zip"
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
        if parse_dependencies(
            download_path[:-4], language, specified_dependencies
        ) or parse_sbom_dependencies(git_group, git_name, specified_dependencies):
            print(f"===>Correct: Found {idx}th project {project['name']}")
            update_time = project["updated_at"]
            create_time = project["created_at"]

            df.loc[idx] = [
                idx,
                git_group,
                git_name,
                language,
                version,
                download_url,
                file_name,
                update_time,
                create_time,
            ]
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


def download_repositories(properties):
    xls_path = os.path.abspath(properties["xls_path"])
    df = get_repo_dependency(xls_path)
    new_df = pd.DataFrame(
        columns=[
            "id",
            "git_group",
            "git_name",
            "language",
            "version",
            "download_url",
            "file_name",
            "update_time",
            "create_time",
        ]
    )
    repo_path = os.path.abspath(properties["repo_path"])
    for index, row in df.iterrows():
        git_group = row["git_group"]
        git_name = row["git_name"]
        if tag_name := get_repo_tag(git_group, git_name):
            version = tag_name
            download_url = f"https://codeload.github.com/{git_group}/{git_name}/zip/refs/tags/{version}"
            file_name = f"{git_name}-{version.replace('/','-')}.zip"
            print(f"===>Correct: {index} Found tag {tag_name} for project {git_name}")
            new_df.loc[index] = [
                index,
                git_group,
                git_name,
                properties["language"],
                version,
                download_url,
                file_name,
                row["update_time"],
                row["create_time"],
            ]
        else:
            version = row["version"]
            download_url = f"https://codeload.github.com/{git_group}/{git_name}/zip/refs/heads/{version}"
            file_name = f"{git_name}-{version.replace('/','-')}.zip"
            print(
                f"===>Correct: {index} keeping the same version {version} for project {git_name}"
            )
            new_df.loc[index] = [
                index,
                git_group,
                git_name,
                properties["language"],
                version,
                download_url,
                file_name,
                row["update_time"],
                row["create_time"],
            ]
            continue

        old_path = os.path.join(repo_path, row["file_name"])
        if os.path.exists(old_path[:-4]):
            shutil.rmtree(old_path[:-4])

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
        print(f"===>Correct: Downloaded project {git_name}")
        if os.path.exists(old_path):
            os.remove(old_path)
    new_df.to_excel(
        os.path.join(xls_path, f"repositories_{properties['language']}_2.xlsx"),
        index=False,
    )


def resolve_dependencies(properties):
    xls_path = os.path.abspath(properties["xls_path"])
    old_df = get_repo_dependency(xls_path)
    new_df = pd.DataFrame(
        columns=[
            "id",
            "git_group",
            "git_name",
            "language",
            "version",
            "download_url",
            "file_name",
            "update_time",
            "create_time",
        ]
    )
    base_url = "https://api.github.com/repos/{}/{}"
    idx = 0
    for _, row in old_df.iterrows():
        git_group = row["git_group"]
        git_name = row["git_name"]
        if "update_time" not in row or "create_time" not in row:
            url = base_url.format(git_group, git_name)
            response_data = make_request(url)
            if not response_data:
                print(f"===>Error: Failed to fetch data from {url}")
                continue
            print(f"===>Correct: {idx} Fetched data from {url}")
            create_time = response_data["created_at"]
            update_time = response_data["updated_at"]
        else:
            create_time = row["create_time"]
            update_time = row["update_time"]
        idx += 1
        new_df.loc[idx] = [
            idx,
            git_group,
            git_name,
            row["language"],
            row["version"],
            row["download_url"],
            row["file_name"],
            update_time,
            create_time,
        ]
    file_path = os.path.join(xls_path, f"repositories_{properties['language']}.xlsx")
    new_df.to_excel(file_path, index=False)
    print(f"===>Correct: Data saved to {file_path}")
