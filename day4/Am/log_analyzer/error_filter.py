"""异常筛选与特征提取模块。"""

import re
import pandas as pd


def extract_module(content: str) -> str:
    """从 error 消息中提取模块名。workerEnv 优先级高于 mod_jk。"""
    if re.search(r'workerEnv', content):
        return 'workerEnv'
    patterns = [
        (r'^mod_jk\b', 'mod_jk'),
        (r'^jk2_init\b', 'jk2_init'),
        (r'^env\.', 'env'),
        (r'^config\.', 'config'),
        (r'^uriMap\b', 'uriMap'),
    ]
    for pat, name in patterns:
        if re.search(pat, content):
            return name
    return 'other'


def extract_error_code(content: str) -> str:
    """从 error 消息中提取错误码。"""
    m = re.search(r'error state (\d+)', content)
    if m:
        return f'mod_jk_state_{m.group(1)}'
    if re.search(r'mod_jk child init', content):
        return 'mod_jk_child_init'
    if re.search(r'^jk2_init\b', content):
        return 'jk2_init'
    if re.search(r'env\.createBean2', content):
        return 'env_createBean'
    if re.search(r'config\.update', content):
        return 'config_update'
    if re.search(r'^uriMap\b', content):
        return 'uriMap'
    if re.search(r'Directory index forbidden', content):
        return 'HTTP_403'
    if re.search(r'File does not exist', content):
        return 'HTTP_404'
    if re.search(r'script not found or unable to stat', content):
        return 'HTTP_500'
    return 'unknown'


def extract_category(content: str) -> str:
    """将错误归入大类。"""
    if re.search(r'\[client\b', content) or re.search(
        r'Directory index forbidden|File does not exist|script not found', content
    ):
        return 'HTTP客户端请求错误'
    return '服务端模块错误'


def enrich_errors(df: pd.DataFrame) -> pd.DataFrame:
    """为 error 行添加 module、error_code、category 特征列。"""
    errors = df[df['level'] == 'error'].copy()
    errors['module'] = errors['content'].apply(extract_module)
    errors['error_code'] = errors['content'].apply(extract_error_code)
    errors['category'] = errors['content'].apply(extract_category)
    return errors


def filter_errors(
    df: pd.DataFrame,
    level: str | None = None,
    keyword: str | None = None,
    module: str | None = None,
    error_code: str | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """多维度筛选异常日志。"""
    result = df
    if level is not None:
        result = result[result['level'] == level]
    if keyword is not None:
        result = result[result['content'].str.contains(keyword, case=False, na=False)]
    if module is not None:
        result = result[result['module'] == module]
    if error_code is not None:
        result = result[result['error_code'] == error_code]
    if category is not None:
        result = result[result['category'] == category]
    return result
