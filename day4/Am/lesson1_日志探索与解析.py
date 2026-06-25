"""Lesson 1：日志探索与解析清洗。"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from log_parser import parse_log_file, LOG_PATTERN

LOG_PATH = os.path.join(os.path.dirname(__file__), 'Apache.log')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), 'structured_logs.csv')


def explore_raw_logs(path: str) -> None:
    """数据探索：统计总行数、各级别日志数量、时间范围、异常行数。"""
    level_counts: dict[str, int] = {}
    abnormal = 0
    total = 0
    timestamps: list[str] = []

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            m = LOG_PATTERN.match(line)
            if m:
                ts, level, _ = m.group(1), m.group(2), m.group(3)
                level_counts[level] = level_counts.get(level, 0) + 1
                timestamps.append(ts)
            else:
                abnormal += 1

    print("=" * 50)
    print("数据探索结果")
    print("=" * 50)
    print(f"总行数（非空）: {total}")
    print(f"标准格式行数:   {total - abnormal}")
    print(f"异常行数:       {abnormal}")
    print()
    print("各级别日志数量:")
    level_counts['unknown'] = abnormal
    for lvl, cnt in sorted(level_counts.items(), key=lambda x: -x[1]):
        print(f"  {lvl:10s}: {cnt}")
    print()
    if timestamps:
        print(f"时间范围: {timestamps[0]} ~ {timestamps[-1]}")
    print()


def main() -> None:
    # 1. 数据探索
    explore_raw_logs(LOG_PATH)

    # 2. 正则解析并保存 CSV
    print("正在解析日志并生成 structured_logs.csv ...")
    df = parse_log_file(LOG_PATH)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"完成！共 {len(df)} 条记录，已保存到 {OUTPUT_CSV}")
    print()
    print("前 5 条记录预览:")
    print(df.head().to_string(index=False))


if __name__ == '__main__':
    main()
