"""统计分析模块。"""

import pandas as pd


def daily_error_count(errors: pd.DataFrame) -> pd.DataFrame:
    """统计每日 Error 数量趋势。"""
    df = errors.copy()
    df['date'] = pd.to_datetime(df['timestamp'], format='%a %b %d %H:%M:%S %Y', errors='coerce').dt.date
    daily = df.groupby('date').size().reset_index(name='error_count')
    return daily.sort_values('date')


def error_code_stats(errors: pd.DataFrame) -> pd.DataFrame:
    """统计各错误码出现次数与占比。"""
    counts = errors['error_code'].value_counts().reset_index()
    counts.columns = ['error_code', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(2)
    return counts


def module_error_stats(errors: pd.DataFrame) -> pd.DataFrame:
    """统计各模块异常数量与异常率。"""
    module_counts = errors.groupby('module').size().reset_index(name='error_count')
    total = len(errors)
    module_counts['total_count'] = total
    module_counts['error_rate'] = (module_counts['error_count'] / total * 100).round(2)
    return module_counts.sort_values('error_count', ascending=False)


def category_stats(errors: pd.DataFrame) -> pd.DataFrame:
    """按大类统计错误数量与占比。"""
    counts = errors['category'].value_counts().reset_index()
    counts.columns = ['category', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(2)
    return counts
