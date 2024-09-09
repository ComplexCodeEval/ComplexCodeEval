import json
from tree_sitter import Language, Parser
import jsonlines

json_data_path = ""

java_data = []
with open(json_data_path, "r", encoding="utf-8") as f:
    java_data = json.load(f)

LANGUAGE = Language("./dataset_extract/parser/my-languages.so", "java")
parser = Parser()
parser.set_language(LANGUAGE)


def analysis_api_code(api_code):
    api_name, right = api_code.split("(")[0], api_code.split("(", 1)[1]
    stack = ["("]
    for i in range(len(right)):
        if right[i] == "(":
            stack.append("(")
        elif right[i] == ")":
            stack.pop()
        if len(stack) == 0:
            api_args = right[:i]
            if len(right) > i:
                right = right[i + 1 :]
            else:
                right = ""
            return api_name, api_args, right


def extract_api(api, root):
    if root is None:
        return None
    for child in root.children:
        if child.type == "method_invocation":
            invocation_name = child.text.decode("utf-8").split("(")[0]
            if api.endswith(invocation_name):
                return (child.start_point, child.end_point)
        result = extract_api(api, child)
        if result is not None:
            return result


def extract_code(api, code):
    global success, fail
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    location = extract_api(api, root_node)
    if location is None:
        print(f"API {api} not found in code")
        return
    else:
        code_lines = code.split("\n")
        above_line = location[0][0]
        below_line = location[1][0] + 1
        left_text = location[0][1]
        right_text = location[1][1] + 1
        left_context = "\n".join(code_lines[:above_line])
        right_context = "\n".join(code_lines[below_line:])
        if above_line + 1 == below_line:
            api_code = code_lines[above_line][left_text:right_text]
        else:
            for i in range(above_line, below_line):
                if i == above_line:
                    api_code = code_lines[i][left_text:]
                elif i == below_line - 1:
                    api_code += code_lines[i][:right_text]
                else:
                    api_code += code_lines[i]
        try:
            api_name, api_args, right = analysis_api_code(api_code)
        except:
            print(f"API {api} analysis failed")
            return
        left_context += "\n" + code_lines[above_line][:left_text]
        right_context = (
            right + code_lines[below_line - 1][right_text:] + "\n" + right_context
        )
        return left_context, api_name, api_args, right_context


def construct_when_to_use(api_name, api_args, left_context, right_context, when):
    when.append(
        {
            "context_pre": left_context,
            "content": api_name + "(" + api_args + ")",
            "context_post": right_context,
        }
    )


def construct_which_to_use(api_name, api_args, left_context, right_context, which):
    left = ".".join(api_name.split(".")[:-1])
    middle = api_name.split(".")[-1]
    which.append(
        {
            "context_pre": left_context + left + ".",
            "content": middle + "(" + api_args + ")",
            "context_post": right_context,
        }
    )


def construct_how_to_use(api_name, api_args, left_context, right_context, how):
    how.append(
        {
            "context_pre": left_context + "\n" + api_name + "(",
            "content": api_args,
            "context_post": ")" + right_context,
        }
    )


def main():
    when = []
    which = []
    how = []
    methods = [construct_when_to_use, construct_which_to_use, construct_how_to_use]
    for data in java_data:
        apis = data["reference_api"]
        code = data["solution"]
        file_left_context = data["left_context"]
        file_left_context = "\n".join(file_left_context.split("\n")[-10:])
        file_right_context = data["right_context"]
        file_right_context = "\n".join(file_right_context.split("\n")[:10])
        comment = data["prompt"]
        import_list = data["import_text"]
        import_context = "\n".join(["import " + i for i in import_list])
        for api in apis:
            try:
                left_context, api_name, api_args, right_context = extract_code(
                    api, code
                )
            except:
                continue
            left_context = (
                import_context
                + "\n"
                + file_left_context
                + "\n"
                + comment
                + "\n"
                + left_context
            )
            right_context = right_context + "\n" + file_right_context
            construct_when_to_use(api_name, api_args, left_context, right_context, when)
            construct_which_to_use(
                api_name, api_args, left_context, right_context, which
            )
            construct_how_to_use(api_name, api_args, left_context, right_context, how)
    with jsonlines.open("when.jsonl", "w") as f:
        f.write_all(when)
    with jsonlines.open("which.jsonl", "w") as f:
        f.write_all(which)
    with jsonlines.open("how.jsonl", "w") as f:
        f.write_all(how)


if __name__ == "__main__":
    main()
