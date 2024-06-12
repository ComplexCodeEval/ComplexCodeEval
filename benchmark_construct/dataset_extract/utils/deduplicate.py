# 当两组api的结果相似度超过一半时，删除其中一组api的结果

def compare_result(result1, result2):
    if (result1["git_group"] == result2["git_group"] and
            result1["git_name"] == result2["git_name"] and
            result1["version"] == result2["version"] and
            result1["project_name"] == result2["project_name"] and
            result1["file_path"] == result2["file_path"] and
            result1["focal_class"] == result2["focal_class"] and
            result1["focal_name"] == result2["focal_name"]):
        return True
    else:
        return False


def add_remove_result(json_result, api):
    baseline = len(api) // 2
    if baseline == 0:
        baseline = 1
    for key in json_result.keys():
        same_result = 0
        for result1 in json_result[key]:
            for result2 in api:
                if compare_result(result1, result2):
                    same_result += 1
        if same_result >= baseline:
            return False
    return True


def analysis_result(json_result):
    api = list(json_result.keys())
    api_remove = {}
    for i in range(len(api)):
        baseline = len(json_result[api[i]]) // 2
        if baseline == 0:
            baseline = 1
        for j in range(i + 1, len(api)):
            same_result = 0
            for result1 in json_result[api[i]]:
                for result2 in json_result[api[j]]:
                    if compare_result(result1, result2):
                        same_result += 1
            if same_result >= baseline:
                api_remove[api[i]] = json_result[api[i]]
                break
    for api in api_remove.keys():
        del json_result[api]
    for api in api_remove.keys():
        if add_remove_result(json_result, api_remove[api]):
            json_result[api] = api_remove[api]
    return len(list(json_result.keys()))
