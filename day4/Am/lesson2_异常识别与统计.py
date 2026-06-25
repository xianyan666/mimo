"""Lesson 2：异常识别与统计分析。"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from log_parser import parse_log_file
from error_filter import enrich_errors, filter_errors
from statistics import daily_error_count, error_code_stats, module_error_stats, category_stats

CSV_PATH = os.path.join(os.path.dirname(__file__), 'structured_logs.csv')
OUTPUT_ERROR_CSV = os.path.join(os.path.dirname(__file__), 'error_logs.csv')
OUTPUT_CODE_STATS = os.path.join(os.path.dirname(__file__), 'error_code_stats.csv')
OUTPUT_MODULE_STATS = os.path.join(os.path.dirname(__file__), 'module_error_stats.csv')


def main() -> None:
    # 读取 Lesson 1 输出
    import pandas as pd
    df = pd.read_csv(CSV_PATH)
    print(f"structured_logs.csv 共 {len(df)} 条记录")
    print()

    # 特征提取：为 error 行添加 module、error_code、category
    errors = enrich_errors(df)
    print(f"Error 日志共 {len(errors)} 条")
    print()

    # ── 1. 按大类统计 ──
    print("=" * 55)
    print("1. 按大类统计（HTTP 客户端请求错误 vs 服务端模块错误）")
    print("=" * 55)
    cat_stats = category_stats(errors)
    print(cat_stats.to_string(index=False))
    print()

    # ── 2. 各错误码出现次数与占比 ──
    print("=" * 55)
    print("2. 各错误码出现次数与占比")
    print("=" * 55)
    code_stats = error_code_stats(errors)
    print(code_stats.to_string(index=False))
    print()

    # ── 3. 各模块异常数量与异常率 ──
    print("=" * 55)
    print("3. 各模块异常数量与异常率")
    print("=" * 55)
    mod_stats = module_error_stats(errors)
    print(mod_stats.to_string(index=False))
    print()

    # ── 4. 每日 Error 数量趋势 ──
    print("=" * 55)
    print("4. 每日 Error 数量趋势")
    print("=" * 55)
    daily = daily_error_count(errors)
    print(daily.to_string(index=False))
    print()

    # ── 5. 三维度筛选示例 ──
    print("=" * 55)
    print("5. 筛选示例：level=error, module=mod_jk")
    print("=" * 55)
    filtered = filter_errors(errors, level='error', module='mod_jk')
    print(f"筛选结果: {len(filtered)} 条")
    print(filtered.head(5).to_string(index=False))
    print()

    # ── 6. 导出统计 CSV ──
    code_stats.to_csv(OUTPUT_CODE_STATS, index=False, encoding='utf-8-sig')
    print(f"错误码统计已导出: {OUTPUT_CODE_STATS}")

    mod_stats.to_csv(OUTPUT_MODULE_STATS, index=False, encoding='utf-8-sig')
    print(f"模块统计已导出: {OUTPUT_MODULE_STATS}")

    # ── 7. 导出异常子集 ──
    errors.to_csv(OUTPUT_ERROR_CSV, index=False, encoding='utf-8-sig')
    print(f"异常子集已导出: {OUTPUT_ERROR_CSV} ({len(errors)} 条)")


if __name__ == '__main__':
    main()
