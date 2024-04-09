# 通过调用api生成注释

from openai import OpenAI, BadRequestError

client = OpenAI(api_key="sk-6299c3276293499d8d55e1c32475fd97", base_url="https://api.deepseek.com/v1")

def gen_comment_from_api(code,method,language):
    try:
        print(f"start gen comment for {method}")
        pre_prompt = f"Here is the {language} code:{code}\n \
                    Generate a {language} Doc Comment for the {language} codes, which used the api of {method}\n \
                     Your response should only be comments, without explanation or formatting. \n \
                     Here is an example of {language} Doc Comment: \n \
                     /**\n \
                      * Description: This method is for ...\n \
                      * \n \
                      * @param ...\n \
                      * @param ...\n \
                      * @return ...\n \
                      */\n "
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "user", "content": pre_prompt},
            ],
            max_tokens=2048,
            temperature=0.7,
            stream=False
        )
    except BadRequestError:
        pre_prompt = f"Here is the {language} code:{code}\n \
                    Generate a {language} Doc Comment for the {language} codes, which used the api of {method}\n \
                     Your response should only be comments, without explanation or formatting. \n \
                     Here is an example of {language} Doc Comment: \n \
                     /**\n \
                      * Description: This method is for ...\n \
                      * \n \
                      * @param ...\n \
                      * @param ...\n \
                      * @return ...\n \
                      */\n "
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "user", "content": pre_prompt},
            ],
            max_tokens=2048,
            temperature=0.7,
            stream=False
        )
    print(f"gen comment for {method} done")
    return response.choices[0].message.content