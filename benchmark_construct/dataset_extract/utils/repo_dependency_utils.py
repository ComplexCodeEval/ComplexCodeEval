# 获取analysis_repo_dependency下的所有xls文件的信息

import pandas as pd
import os
import glob

def get_repo_dependency(xls_path):
    columns_to_keep = ['git_group', 'git_name', 'language', 'version', 'download_url', 'file_name', 'update_time', 'create_time']
    subset_cols = ['git_group', 'git_name', 'language']
    xls_filse = glob.glob(os.path.join(xls_path, '*.xls*'))
    total_df = pd.DataFrame()
    for xls_file in xls_filse:
        df = pd.read_excel(xls_file).filter(columns_to_keep)\
            .sort_values(by='update_time', ascending=False)\
            .drop_duplicates(subset=subset_cols, keep='first')
        total_df = pd.concat([total_df, df], axis=0)
    return total_df.drop_duplicates(subset=subset_cols, keep='first')
