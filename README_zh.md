**其他语言版本: [English](README.md), [中文](README_zh.md).**

## 项目简介

本项目旨在爬取GitHub的高星项目，并解析项目依赖信息，判断其是否依赖于`/setup/profile.yaml`中指定的API，从而构建远程项目依赖表，再从依赖表中获取项目相关信息，并解析项目，生成最终数据集。用户也可自行提供项目依赖表（XLS 或者 XLSX 文件）用户提供的表格应包含如下字段：`git_group`、`git_name`、`language`、`version`、`download_url`、`file_name`、`update_time` 和 `create_time`。一个示例的远程仓库信息表可见[analysis_repo_dependency/analysis_repo_dependency1.xls](analysis_repo_dependency/analysis_repo_dependency1.xls)。

### Java 数据集字段

- `git_group`: 存放项目的 Git 组织或组织。类型为`String`，eg:`ukwa`
- `git_name`: Git 上项目的名称。类型为`String`, eg:`webarchive-discovery`
- `version`: 项目的版本号。类型为`String`, eg:`warc-discovery-3.1.0`
- `language`: 项目使用的编程语言。类型为`String`, eg: `Java`
- `project_name`: 从指定下载路径下载下来的项目名称。类型为`String`, eg:`webarchive-discovery-warc-discovery-3.1.0.zip`
- `file_path`: 源代码仓库中相关焦点类的文件路径。类型为`String`, eg:`/webarchive-discovery-warc-discovery-3.1.0/webarchive-discovery-warc-discovery-3.1.0/warc-indexer/src/main/java/uk/bl/wa/parsers/HtmlFeatureParser.java`
- `focal_module`: 项目的焦点模块。类型为`String`, eg:`warc-indexer`
- `focal_package`: 项目的焦点包。类型为`String`, eg:`uk/bl/wa/parsers`
- `focal_class`: 项目的焦点类。类型为`String`, eg:`HtmlFeatureParser`
- `focal_name`: 项目的焦点方法名称。类型为`String`, eg:`parse`
- `focal_parameter`: 项目的焦点方法参数列表。类型为`List` 
- `solution`: 相关问题的解决方案。注意，这直接来自原始源文件。根据下游任务的类型（代码补全或代码生成）和需要向模型提供的上下文量，用户可以采用和更新提示字段。类型为`String`
- `method_signature`: 目标焦点方法的方法签名。类型为`String`, eg:`@Override\n    public void parse(InputStream stream, ContentHandler handler,\n            Metadata metadata, ParseContext context) throws IOException,\n            SAXException, TikaException`
- `left_context`: 焦点方法之前的源代码。类型为`String`
- `right_context`: 焦点方法之后的源代码（括号结束后）。类型为`String`
- `test_function`: 从原始源代码中提取的测试函数列表，对应于测试焦点方法。类型为`List`
- `class_comment`: 焦点类的类注释，可能为`null`。类型为`String`
- `import_text`: 导入包的列表。类型为`List`
- `prompt`: 可直接用于执行代码生成的提示消息。请注意，该prompt是使用 DeepSeekCoder-33b 生成的注释。我们用于生成代码注释的提示是：“总结以下使用 [框架] 的代码，并生成 [编程语言] 注释。响应应由两部分组成:描述以及块标签。块标签应包括 @param 和 @return。”类型为`String`
- `comment`: 从原文件中提取的焦点方法的文档注释，可能为`null`。类型为`String`
- `prompt_is_gen_from_api`: true = 提示消息由 DeepSeekCoder API 生成；false = 提示消息是代码存储库中的原始代码注释。类型为`Bool`
- `method_dependencies`: `solution`对应的代码中所调用的函数。类型为`List`
- `project_create_time`: 项目创建时间。类型为`Datetime`, eg:`2012-12-20T12:17:14+00:00`
- `project_update_time`: 项目更新时间。类型为`Datetime`, eg:`2024-03-31T14:13:17+00:00`
- `file_create_time`: 文件创建时间。类型为`Datetime`, eg:`2013-03-27T13:42:06Z`
- `file_update_time`: 文件创建时间。类型为`Datetime`, eg:`2020-05-14T13:06:47Z`
- `method_update_time`: 方法的最近一次的修改行或增加行操作的时间。类型为`Datetime`, eg:`2013-03-27T13:42:06Z`
- `license`: 该数据所属项目的许可证，可能为`null`。类型为`dict`, eg:`{
        "key": "agpl-3.0",
        "name": "GNU Affero General Public License v3.0",
        "spdx_id": "AGPL-3.0",
        "url": "https://api.github.com/licenses/agpl-3.0",
        "node_id": "MDc6TGljZW5zZTE="
      }`

### Python 数据集字段

- `git_group`: 存放项目的 Git 组织或组织。类型为`String`，eg: `intel`
- `git_name`: Git 上项目的名称。类型为`String`，eg: `neural-compressor`
- `version`: 项目的版本号。类型为`String`，eg: `v2.6.dev0`
- `language`: 项目使用的编程语言。类型为`String`，eg: `Python`
- `project_name`: 从指定下载路径下载下来的项目名称。类型为`String`，eg: `neural-compressor-v2.6.dev0.zip`
- `file_path`: 源代码仓库中相关焦点函数所在文件的文件路径。类型为`String`，eg: `/neural-compressor-v2.6.dev0/neural-compressor-2.6.dev0/neural_compressor/utils/pytorch.py`
- `file_name`: 文件名称。类型为`String`，eg: `pytorch.py`
- `focal_class`: 项目的焦点类，可能为`null`。类型为`String`，eg: `YamlOutputParser`
- `focal_name`: 项目的焦点函数名称。类型为`String`，eg: `load`
- `focal_parameter`: 项目的焦点函数参数列表。类型为`List`
- `solution`: 相关问题的解决方案。注意，这直接来自原始源文件。根据下游任务的类型（代码补全或代码生成）和需要向模型提供的上下文量，用户可以采用和更新提示字段。类型为`String`
- `function_signature`: 目标焦点函数的函数签名。类型为`String`，eg: `def load(checkpoint_dir=None, model=None, layer_wise=False, history_cfg=None, **kwargs) :`
- `left_context`: 焦点函数之前的源代码。类型为`String`
- `right_context`: 焦点函数之后的源代码。类型为`String`
- `test_function`: 从原始源代码中提取的测试函数列表，对应于测试焦点方法。类型为`List`
- `import_text`: 导入包的列表。类型为`List`
- `prompt`: 可直接用于执行代码生成的提示消息。请注意，该prompt是使用 DeepSeekCoder-33b 生成的注释。我们用于生成代码注释的提示是：“总结以下使用 [框架] 的代码，并生成 [编程语言] 注释。响应应由两部分组成:描述以及块标签。块标签应包括 @param 和 @return。”类型为`String`
- `comment`: 从原文件中提取的焦点函数的文档注释，可能为`null`。类型为`String`
- `prompt_is_gen_from_api`: true = 提示消息由 DeepSeekCoder API 生成；false = 提示消息是代码存储库中的原始代码注释。类型为`Bool`
- `function_dependencies`: `solution`对应的代码中所调用的函数。类型为`List`
- `project_create_time`: 项目创建时间。类型为`Datetime`，eg: `2020-07-21T23:49:56+00:00`
- `project_update_time`: 项目更新时间。类型为`Datetime`，eg: `2024-04-18T02:58:11+00:00`
- `file_create_time`: 文件创建时间。类型为`Datetime`，eg: `2021-09-24T08:43:20Z`
- `file_update_time`: 文件更新时间。类型为`Datetime`，eg: `2024-03-22T07:27:34Z`
- `function_update_time`: 函数的最近一次的修改行或增加行操作的时间。类型为`Datetime`，eg: `2023-09-25T10:14:14Z`
- `license`: 该数据所属项目的许可证，可能为`null`。类型为`dict`, eg:`{
        "key": "agpl-3.0",
        "name": "GNU Affero General Public License v3.0",
        "spdx_id": "AGPL-3.0",
        "url": "https://api.github.com/licenses/agpl-3.0",
        "node_id": "MDc6TGljZW5zZTE="
      }`

### 功能特点

- 爬取GitHub高星项目，并分析其依赖情况
- 从远程仓库信息表中获取项目信息，并下载项目。
- 解析项目，分析出其中的 API 调用情况。
- 根据对应框架的 API 调用频率，再次解析项目，提取出对应api的包含测试函数的数据集。
- 支持 Python 和 Java 项目的解析。

### 如何使用

运行工具
```sh
git clone https://github.com/jiafeng0527/dataset_extract.git  
cd ./dataset_extract  
python3 -m dataset_extract  
```
最终会在`./analysis_repo_dependency`中生成远程信息依赖表，在`./repositories`中存放下载的远程仓库，在`./csv_files`中生成以每个框架（包）为单位的对应api的调用情况，`./json_files`中生成以每个框架（包）为单位的最终数据集

### 配置文件
可自行更改配置文件[setup/profile.yaml](setup/profile.yaml)。

### 注意事项

- 项目将会下载远程仓库中的文件，请确保提供的下载链接是可访问的。
- 下载的项目文件需要符合`utf-8`的格式，以便项目能够正确解析。
- 工具只能在项目的当前目录下运行，其他目录下运行会报路径错误。
