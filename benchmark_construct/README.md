## Project Introduction

The aim of this project is to crawl high-star GitHub projects, parse their dependency information, determine whether they depend on the APIs specified in `/setup/profile.yaml`, build a remote project dependency table, then retrieve project-related information from the dependency table, parse the projects, and generate the final dataset. Users can also provide project dependency tables (XLS or XLSX files). The tables provided by users should include the following fields: `git_group`, `git_name`, `language`, `version`, `download_url`, `file_name`, `update_time`, and `create_time`. An example of the remote repository information table can be found at [analysis_repo_dependency/analysis_repo_dependency.xls](analysis_repo_dependency/java_repo_dependency.xlsx).

### Java Dataset Fields

- `git_group`: The Git organization or group where the project is hosted. Type is `String`, e.g., `ukwa`.
- `git_name`: The name of the project on Git. Type is `String`, e.g., `webarchive-discovery`.
- `version`: The version number of the project. Type is `String`, e.g., `warc-discovery-3.1.0`.
- `language`: The programming language used in the project. Type is `String`, e.g., `Java`.
- `project_name`: The name of the project as downloaded from the specified download path. Type is `String`, e.g., `webarchive-discovery-warc-discovery-3.1.0.zip`.
- `file_path`: The file path of the relevant focal class in the source code repository. Type is `String`, e.g., `/webarchive-discovery-warc-discovery-3.1.0/webarchive-discovery-warc-discovery-3.1.0/warc-indexer/src/main/java/uk/bl/wa/parsers/HtmlFeatureParser.java`.
- `focal_module`: The focal module of the project. Type is `String`, e.g., `warc-indexer`.
- `focal_package`: The focal package of the project. Type is `String`, e.g., `uk/bl/wa/parsers`.
- `focal_class`: The focal class of the project. Type is `String`, e.g., `HtmlFeatureParser`.
- `focal_name`: The name of the focal method in the project. Type is `String`, e.g., `parse`.
- `focal_parameter`: The list of parameters for the focal method. Type is `List`.
- `solution`: The solution to the relevant problem. Note that this is directly from the original source file. Depending on the type of downstream task (code completion or code generation) and the amount of context needed to be provided to the model, the user can adopt and update the prompt field. Type is `String`.
- `method_signature`: The method signature of the target focal method. Type is `String`, e.g., `@Override\n    public void parse(InputStream stream, ContentHandler handler,\n            Metadata metadata, ParseContext context) throws IOException,\n            SAXException, TikaException`.
- `left_context`: The source code before the focal method. Type is `String`.
- `right_context`: The source code after the focal method (after the closing bracket). Type is `String`.
- `test_function`: A list of test functions extracted from the original source code, corresponding to the test focal method. Type is `List`.
- `class_comment`: The class comment for the focal class, which may be `null`. Type is `String`.
- `import_text`: A list of imported packages. Type is `List`.
- `prompt`: A prompt message that can be used directly for code generation. Please note that this prompt is generated using the comments from DeepSeekCoder-33b. The prompt we use for generating code comments is: "Summarize the following code using [framework] and generate [programming language] comments. The response should be composed of two parts: description and block tags. Block tags should include @param and @return." Type is `String`.
- `comment`: The documentation comment for the focal method extracted from the original file, which may be `null`. Type is `String`.
- `prompt_is_gen_from_api`: `true` = The prompt message is generated by the DeepSeekCoder API; `false` = The prompt message is the original code comment from the code repository. Type is `Bool`.
- `method_dependencies`: The functions called in the code corresponding to `solution`. Type is `List`.
- `project_create_time`: The creation time of the project. Type is `Datetime`, e.g., `2012-12-20T12:17:14+00:00`.
- `project_update_time`: The update time of the project. Type is `Datetime`, e.g., `2024-03-31T14:13:17+00:00`.
- `file_create_time`: The creation time of the file. Type is `Datetime`, e.g., `2013-03-27T13:42:06Z`.
- `file_update_time`: The update time of the file. Type is `Datetime`, e.g., `2020-05-14T13:06:47Z`.
- `method_update_time`: The most recent time of modification or addition to the lines of the method. Type is `Datetime`, e.g., `2013-03-27T13:42:06Z`.
- `license`:  The license of the project to which this data belongs, which may be null. The type is dict, e.g., `{
        "key": "agpl-3.0",
        "name": "GNU Affero General Public License v3.0",
        "spdx_id": "AGPL-3.0",
        "url": "https://api.github.com/licenses/agpl-3.0",
        "node_id": "MDc6TGljZW5zZTE="
      }`

### Python Dataset Fields

- `git_group`: The Git organization or group where the project is hosted. Type is `String`, e.g., `intel`.
- `git_name`: The name of the project on Git. Type is `String`, e.g., `neural-compressor`.
- `version`: The version number of the project. Type is `String`, e.g., `v2.6.dev0`.
- `language`: The programming language used in the project. Type is `String`, e.g., `Python`.
- `project_name`: The name of the project as downloaded from the specified download path. Type is `String`, e.g., `neural-compressor-v2.6.dev0.zip`.
- `file_path`: The file path of the relevant focal function in the source code repository. Type is `String`, e.g., `/neural-compressor-v2.6.dev0/neural-compressor-2.6.dev0/neural_compressor/utils/pytorch.py`.
- `file_name`: The name of the file. Type is `String`, e.g., `pytorch.py`.
- `focal_class`: The focal class of the project, which may be `null`. Type is `String`, e.g., `YamlOutputParser`.
- `focal_name`: The name of the focal function in the project. Type is `String`, e.g., `load`.
- `focal_parameter`: The list of parameters for the focal function. Type is `List`.
- `solution`: The solution to the relevant problem. Note that this is directly from the original source file. Depending on the type of downstream task (code completion or code generation) and the amount of context needed to be provided to the model, the user can adopt and update the prompt field. Type is `String`.
- `function_signature`: The function signature of the target focal function. Type is `String`, e.g., `def load(checkpoint_dir=None, model=None, layer_wise=False, history_cfg=None, **kwargs) :`.
- `left_context`: The source code before the focal function. Type is `String`.
- `right_context`: The source code after the focal function. Type is `String`.
- `test_function`: A list of test functions extracted from the original source code, corresponding to the test focal method. Type is `List`.
- `import_text`: A list of imported packages. Type is `List`.
- `prompt`: A prompt message that can be used directly for code generation. Please note that this prompt is generated using the comments from DeepSeekCoder-33b. The prompt we use for generating code comments is: "Summarize the following code using [framework] and generate [programming language] comments. The response should be composed of two parts: description and block tags. Block tags should include @param and @return." Type is `String`.
- `comment`: The documentation comment for the focal function extracted from the original file, which may be `null`. Type is `String`.
- `prompt_is_gen_from_api`: `true` = The prompt message is generated by the DeepSeekCoder API; `false` = The prompt message is the original code comment from the code repository. Type is `Bool`.
- `function_dependencies`: The functions called in the code corresponding to `solution`. Type is `List`.
- `project_create_time`: The creation time of the project. Type is `Datetime`, e.g., `2020-07-21T23:49:56+00:00`.
- `project_update_time`: The update time of the project. Type is `Datetime`, e.g., `2024-04-18T0`.
- `file_create_time`: The creation time of the file. Type is `Datetime`, e.g., `2013-03-27T13:42:06Z`.
- `file_update_time`: The update time of the file. Type is `Datetime`, e.g., `2020-05-14T13:06:47Z`.
- `method_update_time`: The most recent time of modification or addition to the lines of the method. Type is `Datetime`, e.g., `2013-03-27T13:42:06Z`.
- `license`:  The license of the project to which this data belongs, which may be null. The type is dict, e.g., `{
        "key": "agpl-3.0",
        "name": "GNU Affero General Public License v3.0",
        "spdx_id": "AGPL-3.0",
        "url": "https://api.github.com/licenses/agpl-3.0",
        "node_id": "MDc6TGljZW5zZTE="
      }`

### An Example of samples

![sample_example](../figures/sample_example.png)

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
The final output will include a remote information dependency table generated in the `./analysis_repo_dependency` directory, the downloaded remote repositories stored in the `./repositories` directory, the API call details for each framework (package) generated in the `./csv_files` directory, and the final dataset for each framework (package) generated in the `./json_files` directory.

### Configuration File

The configuration file can be customized at [setup/profile.yaml](setup/profile.yaml).

### Prompt used to Generate docstring

![prompt_template](../figures/prompt_template.png)

### Notes

- The tool will download files from remote repositories, so ensure that the provided download links are accessible.
- Downloaded project files should be in UTF-8 format for proper parsing.
- The tool must be run in the project's current directory; running it in other directories will result in path errors.
