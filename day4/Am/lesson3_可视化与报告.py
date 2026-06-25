"""Lesson 3：可视化展示与报告总结 — 演示脚本。"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from log_analyzer import (
    safe_read_csv, enrich_errors,
    daily_error_count, error_code_stats, module_error_stats, category_stats,
    plot_daily_error_trend, plot_error_code_pie, plot_module_error_bar,
    ensure_dir, CHARTS_DIR,
)

CSV_PATH = os.path.join(os.path.dirname(__file__), 'structured_logs.csv')


def main() -> None:
    # 0. 准备
    ensure_dir(CHARTS_DIR)

    # 1. 读取数据
    print("读取 structured_logs.csv ...")
    df = safe_read_csv(CSV_PATH)
    print(f"共 {len(df)} 条记录\n")

    # 2. 特征提取
    errors = enrich_errors(df)
    print(f"Error 日志: {len(errors)} 条\n")

    # 3. 统计
    print("=" * 50)
    print("统计结果")
    print("=" * 50)

    cat = category_stats(errors)
    print("\n[大类统计]")
    print(cat.to_string(index=False))

    codes = error_code_stats(errors)
    print("\n[错误码统计 Top 10]")
    print(codes.head(10).to_string(index=False))

    modules = module_error_stats(errors)
    print("\n[模块统计]")
    print(modules.to_string(index=False))

    daily = daily_error_count(errors)
    print(f"\n[每日趋势] 共 {len(daily)} 天，"
          f"日均 {daily['error_count'].mean():.0f} 条，"
          f"峰值 {daily['error_count'].max()} 条")

    # 4. 生成图表
    print("\n" + "=" * 50)
    print("生成图表")
    print("=" * 50)

    p1 = plot_daily_error_trend(daily)
    print(f"  {p1}")

    p2 = plot_error_code_pie(codes, top_n=8)
    print(f"  {p2}")

    p3 = plot_module_error_bar(modules)
    print(f"  {p3}")

    print(f"\n图表已保存到 {CHARTS_DIR}")
    print("完成！")


if __name__ == '__main__':
    main()
