import requests
from datetime import datetime
from time import sleep
import urllib.parse

# GitHub API tokens
tokens = []

# 初始化全局变量
token_index = 0
remaining_points = 0
last_request_time = datetime.now()
failed_tokens = set()  # 记录遇到 403 错误的 token


def get_remaining_points(headers):
    global remaining_points, last_request_time
    remaining_points = int(headers.get("X-RateLimit-Remaining", 0))
    reset_time = int(headers.get("X-RateLimit-Reset", datetime.now().timestamp()))
    last_request_time = (
        datetime.now() if remaining_points == 0 else datetime.fromtimestamp(reset_time)
    )


def get_token():
    global token_index
    if tokens == []:
        return None
    token_index = (token_index + 1) % len(tokens)
    return tokens[token_index]


def make_request(url):
    global last_request_time, failed_tokens
    max_retry = 5
    url = urllib.parse.quote(url, safe=":/?&=+")
    while max_retry > 0:
        try:
            headers = {
                "Authorization": f"token {get_token()}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = requests.get(url, headers=headers, timeout=10)
            break
        except Exception as e:
            max_retry -= 1
            print(f"--->Error: Failed to make request to {url}: {e}")
            sleep(10)
    get_remaining_points(response.headers)
    if response.status_code == 401:
        print(f"--->Error: Received 401 error. Retrying with new token...")
        return make_request(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        print(f"--->Error: Received 403 error. Retrying with new token...")
        failed_tokens.add(headers["Authorization"].split()[1])
        if len(failed_tokens) == len(tokens):
            sleep_time = min(
                (last_request_time - datetime.now()).seconds + 1 for _ in tokens
            )
            print(
                f"--->Error: All tokens encountered 403 errors. Waiting until {last_request_time}"
            )
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
                "Authorization": f"token {get_token()}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = requests.get(url, headers=headers, timeout=10)
            break
        except Exception as e:
            max_retry -= 1
            print(f"--->Error: Failed to make request to {url}: {e}")
            sleep(10)
    get_remaining_points(response.headers)
    if response.status_code == 200:
        if "next" in response.links:
            next_url = response.links["next"]["url"]
            next_response = make_rest_request(next_url)
            if next_response:
                return response.json()["items"] + (next_response)
            return response.json()["items"]
        return response.json()["items"]
    elif response.status_code == 403:
        print(f"--->Error: Received 403 error. Retrying with new token...")
        failed_tokens.add(headers["Authorization"].split()[1])
        if len(failed_tokens) == len(tokens):
            sleep_time = min(
                (last_request_time - datetime.now()).seconds + 1 for _ in tokens
            )
            print(
                f"--->Error: All tokens encountered 403 errors. Waiting until {last_request_time}"
            )
            sleep(sleep_time)
            failed_tokens.clear()
        return make_rest_request(url)
    else:
        print(f"--->Error: Failed to make request to {url}: {response.status_code}")
        return None


def make_graphql_request(query, variables):
    global last_request_time, failed_tokens
    data = {"query": query, "variables": variables}
    max_retry = 5
    while True:
        try:
            headers = {
                "Authorization": f"token {get_token()}",
                "Accept": "application/json",
            }
            response = requests.post(
                "https://api.github.com/graphql", json=data, headers=headers, timeout=10
            )
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
        failed_tokens.add(headers["Authorization"].split()[1])
        if len(failed_tokens) == len(tokens):
            sleep_time = min(
                (last_request_time - datetime.now()).seconds + 1 for _ in tokens
            )
            print(
                f"--->Error: All tokens encountered 403 errors. Waiting until {last_request_time}"
            )
            sleep(sleep_time)
            failed_tokens.clear()
        return make_graphql_request(query, variables)
    else:
        print(
            f"--->Error: Failed to make request to GraphQL API: {response.status_code}"
        )
        return None
