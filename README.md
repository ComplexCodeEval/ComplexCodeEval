**Read this in other languages: [English](README.md), [中文](README_zh.md).**

## Project Introduction

The aim of this project is to crawl high-star GitHub projects, parse their dependency information, determine whether they depend on the APIs specified in `/setup/profile.yaml`, build a remote project dependency table, then retrieve project-related information from the dependency table, parse the projects, and generate the final dataset. Users can also provide project dependency tables (XLS or XLSX files). The tables provided by users should include the following fields: `git_group`, `git_name`, `language`, `version`, `download_url`, `file_name`, `update_time`, and `create_time`. An example of the remote repository information table can be found at [analysis_repo_dependency/analysis_repo_dependency1.xls](analysis_repo_dependency/analysis_repo_dependency1.xls).

### Fields for Java Dataset

- `git_group`: Git group or organization where the project is located.
- `git_name`: Name of the project in Git.
- `version`: Version number of the project.
- `language`: Programming language used in the project.
- `project_name`: Name of the project.
- `create_time`: Time when the project was created.
- `update_time`: Time when the project was last updated.
- `file_path`: File path of the relevant focal class in its original repository.
- `focal_module`: Focal module of the project.
- `focal_package`: Focal package of the project.
- `focal_class`: Focal class of the project.
- `focal_name`: Focal method name of the project.
- `focal_parameter`: Focal parameter list.
- `solution`: Solution of the related problem. Note that this is taken directly from the original source file. Depending on the type of downstream tasks (code completion or code generation) and the amount of context that needs to be provided to the model, users can adopt and update the prompt field accordingly.
- `method_signature`: Method signature of the target focal method.
- `left_context`: Source code before the focal method.
- `right_context`: Source code after the focal method (after the ending parenthesis).
- `test_function`: List of test functions extracted from the original source code, correspond to testing the focal method.
- `class_comment`: Class comment of the focal class.
- `import_text`: List of import packages.
- `prompt`: Prompt message that can be used directly to perform code generation. Note that if the original source code does not have code annotation/comments, we utilize DeepSeekCoder to generate the annotation. The prompt that we use to generate the code comments is “Summarize the following code that uses [framework] and generate the [programming language] comments. The response should be made up of two parts – a description followed by block tags. The block tags should include @param and @return.”
- `prompt_is_gen_from_api`: true = the prompt message is generated from DeepSeekCoder API; false = the prompt message is the original code annotation/comment from the code repository.
- `method_dependencies`: The functions called in the code corresponding to `solution`.

### Fields for Python Dataset

- `git_group`: Git group or organization where the project is located.
- `git_name`: Name of the project in Git.
- `version`: Version number of the project.
- `language`: Programming language used in the project.
- `project_name`: Name of the project.
- `create_time`: Time when the project was created.
- `update_time`: Time when the project was last updated.
- `file_path`: File path of the relevant focal class in its original repository.
- `file_name`: File name.
- `focal_class`: Focal class of the project.
- `focal_name`: Focal function name of the project.
- `focal_parameter`: Focal parameter list.
- `solution`: Solution of the related problem. Note that this is taken directly from the original source file. Depending on the type of downstream tasks (code completion or code generation) and the amount of context that needs to be provided to the model, users can adopt and update the prompt field accordingly.
- `function_signature`: Function signature of the target focal function.
- `left_context`: Source code before the focal function.
- `right_context`: Source code after the focal function.
- `test_function`: List of test functions extracted from the original source code, correspond to testing the focal method.
- `import_text`: List of import texts.
- `prompt`: Prompt message that can be used directly to perform code generation. Note that if the original source code does not have code annotation/comments, we utilize DeepSeekCoder to generate the annotation. The prompt that we use to generate the code comments is “Summarize the following code that uses [framework] and generate the [programming language] comments. The response should be made up of two parts – a description followed by block tags. The block tags should include @param and @return.”
- `prompt_is_gen_from_api`: true = the prompt message is generated from DeepSeekCoder API; false = the prompt message is the original code annotation/comment from the code repository.
- `function_dependencies`: Functions called in the code corresponding to `solution`.

### Key Features

- Crawl high-star GitHub projects and analyze their dependencies.
- Obtain project information from the remote repository information table and download projects.
- Parse projects and analyze API call situations.
- Based on the API call frequency of the corresponding framework, extract datasets containing test functions.
- Support parsing of Python and Java projects.

### How to Use

Run the tool:
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
