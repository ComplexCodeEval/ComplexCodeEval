# 通过调用api生成注释

from openai import OpenAI, BadRequestError

# api_key: deepseek api key
client = OpenAI(api_key="", base_url="https://api.deepseek.com/v1")
Doc_Comment = {
    "Java": "/**\n * Description: This method is for ...\n * \n * @param ...\n * @param ...\n * @return ...\n */",
    "Python": '"""\nDescription: This function is for ...\n\nArgs:\n    param1 (type): Description of param1\n    param2 (type): Description of param2\n    ...\n\nReturns:\n    type: Description of the return value\n"""',
    "Go": "// Description: This function is for ...\n//\n// Params:\n//    param1: Description of param1\n//    param2: Description of param2\n//    ...\n//\n// Returns:\n//    Description of the return value",
}


def gen_comment_from_api(code, method, language):
    try:
        print(f"start gen comment for {method}")
        pre_prompt = (
            f"Here is the {language} code:",
            f"'''{language}",
            f"{code}",
            f"'''",
            f"Generate a {language} Doc Comment for the {language} code, which uses the API of {method}.",
            f"Generate the code comment in such a way that it is suitable to be used as a prompt for code generation.",
            f"Your response should only include the docstring, without explanation or formatting.",
            f"Here is an example of {language} Doc Comment:",
            f"'''{language}",
            f"{Doc_Comment[language]}",
            f"'''",
        )
        pre_prompt = "\n".join(pre_prompt)
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "user", "content": pre_prompt},
            ],
            max_tokens=2048,
            temperature=0,
            stream=False,
        )
    except BadRequestError:
        pre_prompt = (
            f"Here is the {language} code:",
            f"'''{language}",
            f"{code}",
            f"'''",
            f"Generate a {language} Doc Comment for the {language} code, which uses the API of {method}.",
            f"Generate the code comment in such a way that it is suitable to be used as a prompt for code generation.",
            f"Your response should only include the docstring, without explanation or formatting.",
            f"Here is an example of {language} Doc Comment:",
            f"'''{language}",
            f"{Doc_Comment[language]}",
            f"'''",
        )
        pre_prompt = "\n".join(pre_prompt)
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "user", "content": pre_prompt},
            ],
            max_tokens=2048,
            temperature=0,
            stream=False,
        )
    print(f"gen comment for {method} done")
    return response.choices[0].message.content
