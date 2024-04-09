**Read this in other languages: [English](README.md), [中文](README_zh.md).**

## Project Introduction

This project aims to download projects from remote repositories based on the provided repository information table (XLS or XLSX file), parse the projects, and generate datasets. The provided table should contain the following fields: `git_group`, `git_name`, `language`, `version`, `download_url`, `file_name`, `update_time`, and `create_time`.An example of a remote repository information table can be found in [analysis_repo_dependency/analysis_repo_dependency1.xls](analysis_repo_dependency/analysis_repo_dependency1.xls).

### Fields for Java Dataset

- `git_group`: Git group or organization where the project is located.
- `git_name`: Name of the project in Git.
- `version`: Version number of the project.
- `language`: Programming language used in the project.
- `project_name`: Name of the project.
- `create_time`: Time when the project was created.
- `update_time`: Time when the project was last updated.
- `file_path`: File path.
- `focal_module`: Focal module of the project.
- `focal_package`: Focal package of the project.
- `focal_class`: Focal class of the project.
- `focal_name`: Focal name.
- `focal_parameter`: Focal parameter list.
- `solution`: Solution.
- `method_signature`: Method signature.
- `left_context`: Left context.
- `right_context`: Right context.
- `test_function`: List of test functions.
- `class_comment`: Class comment.
- `import_text`: List of import texts.
- `prompt`: Prompt message.
- `prompt_is_gen_from_api`: Indicates whether the prompt message is generated from the API.

### Fields for Python Dataset

- `git_group`: Git group or organization where the project is located.
- `git_name`: Name of the project in Git.
- `version`: Version number of the project.
- `language`: Programming language used in the project.
- `project_name`: Name of the project.
- `create_time`: Time when the project was created.
- `update_time`: Time when the project was last updated.
- `file_path`: File path.
- `file_name`: File name.
- `focal_class`: Focal class of the project.
- `focal_name`: Focal name.
- `focal_parameter`: Focal parameter list.
- `solution`: Solution.
- `function_signature`: Function signature.
- `left_context`: Left context.
- `right_context`: Right context.
- `test_function`: List of test functions.
- `import_text`: List of import texts.
- `prompt`: Prompt message.
- `prompt_is_gen_from_api`: Indicates whether the prompt message is generated from the API.

### Key Features

- Obtain project information from the remote repository information table and download projects.
- Parse projects and analyze API call situations.
- Based on the API call frequency of the corresponding framework, extract datasets containing test functions.
- Support parsing of Python and Java projects.

### How to Use

1. Prepare the remote repository information table and place it in the path specified by `/setup/profile.yaml`.
2. Run the tool:
```sh
python3 -m dataset_extract
```

### Output Example

A default output example:
- Three folders `./csv_files`, `./json_files`, and `./repositories` will be generated in the current directory.
- The `./repositories` folder stores all projects from the remote repository information table, similar to the following image:  
![Example of /repositories](example/image0.png)
- The `./csv_files` folder stores the API call information for all projects in the remote repository information table. For each API specified in [setup/profile.yaml](setup/profile.yaml), `{language}_{API}_repo_acount.csv` and `{language}_{API}_repo_acount_analysis.csv` will be created, similar to the following images:  
![Example of /csv_files](example/image1.png)
  - Example of `{language}_{API}_repo_acount.csv`:  
  ![Example of repo_acount](example/image2.png)
  - Example of `{language}_{API}_repo_acount_analysis.csv`:  
  ![Example of repo_acount_analysis](example/image3.png)
- The `./json_files` folder stores the final datasets. For each API specified in [setup/profile.yaml](setup/profile.yaml), `{language}_{api}_comment_tested_API_1.json` will be created, similar to the following image:  
![Example of /json_files](example/image4.png)
  - Example of `{language}_{api}_comment_tested_API_1.json`:  
  ![Example of comment_tested_API](example/image5.png)

### Configuration File

The configuration file can be customized at [setup/profile.yaml](setup/profile.yaml).

### Notes

- The tool will download files from remote repositories, so ensure that the provided download links are accessible.
- Downloaded project files should be in UTF-8 format for proper parsing.
- The tool must be run in the project's current directory; running it in other directories will result in path errors.
