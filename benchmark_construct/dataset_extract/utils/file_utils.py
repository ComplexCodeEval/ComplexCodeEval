# 文件相关工具

import os


def get_java_files(path):
    java_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    return java_files


def get_python_files(path):
    python_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files
