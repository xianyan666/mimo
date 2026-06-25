#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
408考研学习助手 - CLI主程序

帮助用户记录、跟踪和分析408考研学习进度。

用法：
    python cli.py submit    提交学习记录
    python cli.py today     查看今日记录
    python cli.py check     查看整体进度
    python cli.py review    生成复盘报告
    python cli.py config    管理配置
"""

import sys
import os
import io
import argparse

# Windows终端UTF-8编码支持
if sys.platform == "win32":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commands import submit, today, check, review, config_cmd


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="408-assistant",
        description="408考研学习助手 - 记录和分析你的学习进度",
        epilog="示例：\n  python cli.py submit    提交今日学习记录\n  python cli.py check     查看学习进度",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    submit_parser = subparsers.add_parser("submit", help="提交学习记录")
    submit_parser.set_defaults(func=submit.execute)

    today_parser = subparsers.add_parser("today", help="查看今日记录")
    today_parser.set_defaults(func=today.execute)

    check_parser = subparsers.add_parser("check", help="查看整体进度")
    check_parser.set_defaults(func=check.execute)

    review_parser = subparsers.add_parser("review", help="生成复盘报告")
    review_parser.set_defaults(func=review.execute)

    config_parser = subparsers.add_parser("config", help="管理配置")
    config_parser.add_argument("--set", type=str, help="设置配置项")
    config_parser.add_argument("value", nargs="?", help="配置值")
    config_parser.set_defaults(func=config_cmd.execute)

    return parser


def ensure_data_dir():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"[成功] 已创建数据目录：{data_dir}")


def main():
    ensure_data_dir()

    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n[提示] 使用 python cli.py submit 开始记录学习")
        return

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n[警告] 操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 发生错误：{e}")
        print("如问题持续，请检查 data/ 目录权限")
        sys.exit(1)


if __name__ == "__main__":
    main()
