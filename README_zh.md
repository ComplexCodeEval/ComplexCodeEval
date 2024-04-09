**其他语言版本: [English](README.md), [中文](README_zh.md).**

## 项目简介

本项目旨在通过用户提供的远程仓库信息表（XLS 或者 XLSX 文件），从指定的下载链接下载项目，并解析项目，最终生成数据集。用户提供的表格应包含如下字段：`git_group`、`git_name`、`language`、`version`、`download_url`、`file_name`、`update_time` 和 `create_time`。一个示例的远程仓库信息表可见[analysis_repo_dependency/analysis_repo_dependency1.xls](analysis_repo_dependency/analysis_repo_dependency1.xls)。

### Java 数据集字段

- `git_group`: 项目所在的 Git 分组或组织。
- `git_name`: 项目在 Git 中的名称。
- `version`: 项目的版本号。
- `language`: 项目使用的编程语言。
- `project_name`: 项目的名称。
- `create_time`: 项目创建时间。
- `update_time`: 项目最后更新时间。
- `file_path`: 文件路径。
- `focal_module`: 项目的焦点模块。
- `focal_package`: 项目的焦点包。
- `focal_class`: 项目的焦点类。
- `focal_name`: 焦点名称。
- `focal_parameter`: 焦点参数列表。
- `solution`: 解决方案。
- `method_signature`: 方法签名。
- `left_context`: 左侧上下文。
- `right_context`: 右侧上下文。
- `test_function`: 测试函数列表。
- `class_comment`: 类注释。
- `import_text`: 导入文本列表。
- `prompt`: 提示信息。
- `prompt_is_gen_from_api`: 提示信息是否由 API 生成。

### Python 数据集字段

- `git_group`: 项目所在的 Git 分组或组织。
- `git_name`: 项目在 Git 中的名称。
- `version`: 项目的版本号。
- `language`: 项目使用的编程语言。
- `project_name`: 项目的名称。
- `create_time`: 项目创建时间。
- `update_time`: 项目最后更新时间。
- `file_path`: 文件路径。
- `file_name`: 文件名。
- `focal_class`: 项目的焦点类。
- `focal_name`: 焦点名称。
- `focal_parameter`: 焦点参数列表。
- `solution`: 解决方案。
- `function_signature`: 函数签名。
- `left_context`: 左侧上下文。
- `right_context`: 右侧上下文。
- `test_function`: 测试函数列表。
- `import_text`: 导入文本列表。
- `prompt`: 提示信息。
- `prompt_is_gen_from_api`: 提示信息是否由 API 生成。


### 功能特点

- 从远程仓库信息表中获取项目信息，并下载项目。
- 解析项目，分析出其中的 API 调用情况。
- 根据对应框架的 API 调用频率，再次解析项目，提取出对应api的包含测试函数的数据集。
- 支持 Python 和 Java 项目的解析。

### 如何使用

1. 用户准备远程仓库信息表，将其放入`/setup/profile.yaml`指定的`xls_path`的路径中。
2. 运行工具
```sh
python3 -m dataset_extract
```

### 输出示例

一个默认的输出示例：
- 会在当前目录下生成三个文件夹`./csv_files`、`./json_files`、`./repositories`。
- `./repositories`存放了远程仓库信息表中的所有项目，类似于下图：  
![/repositories示例](example/image0.png)
- `./csv_files`存放了在远程仓库信息表中的所有项目的api调用情况，其中会为[setup/profile.yaml](setup/profile.yaml)中提供的所有需要提取的API分别创建一个`{language}_{API}_repo_acount.csv`和`{language}_{API}_repo_acount_analysis.csv`类似于下图：  
![/csv_files示例](example/image1.png)
  - `{language}_{API}_repo_acount.csv`的示例图如下：  
  ![repo_acount示例](example/image2.png)
  - `{language}_{API}_repo_acount_analysis.csv`的示例图如下：  
  ![repo_acount_analysis示例](example/image3.png)
- `./json_files`存放了最终数据集，其中会为[setup/profile.yaml](setup/profile.yaml)中提供的所有需要提取的API分别创建一个`{language}_{api}_comment_tested_API_1.json`，类似于下图：  
![/json_files示例](example/image4.png)
  - `{language}_{api}_comment_tested_API_1.json`的示例图如下：  
  ![comment_tested_API示例](example/image5.png)

### 配置文件
可自行更改配置文件[setup/profile.yaml](setup/profile.yaml)。

### 注意事项

- 项目将会下载远程仓库中的文件，请确保提供的下载链接是可访问的。
- 下载的项目文件需要符合`utf-8`的格式，以便项目能够正确解析。
- 工具只能在项目的当前目录下运行，其他目录下运行会报路径错误。
