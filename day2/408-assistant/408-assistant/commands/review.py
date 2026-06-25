from datetime import date, timedelta

from storage.memory_store import MemoryStore
from storage.config_store import ConfigStore
from core.analyzer import Analyzer
from core.weakness import WeaknessCalculator


def prompt_date_range() -> tuple[str, str]:
    print("\n请选择时间范围：")
    print("  1. 最近7天")
    print("  2. 最近14天")
    print("  3. 最近30天")
    print("  4. 自定义范围")

    while True:
        choice = input("\n请输入选项 (1-4): ").strip()
        today = date.today()

        if choice == "1":
            start = (today - timedelta(days=7)).isoformat()
            return start, today.isoformat()
        elif choice == "2":
            start = (today - timedelta(days=14)).isoformat()
            return start, today.isoformat()
        elif choice == "3":
            start = (today - timedelta(days=30)).isoformat()
            return start, today.isoformat()
        elif choice == "4":
            while True:
                start = input("请输入开始日期 (YYYY-MM-DD): ").strip()
                try:
                    date.fromisoformat(start)
                    break
                except ValueError:
                    print("[错误] 日期格式错误，请使用YYYY-MM-DD格式")
            while True:
                end = input("请输入结束日期 (YYYY-MM-DD): ").strip()
                try:
                    date.fromisoformat(end)
                    break
                except ValueError:
                    print("[错误] 日期格式错误，请使用YYYY-MM-DD格式")
            return start, end
        else:
            print("[错误] 请输入1-4的数字")


def execute(args=None):
    memory_store = MemoryStore()
    config_store = ConfigStore()
    config = config_store.load_config()
    all_records = memory_store.get_all_records()

    print("━" * 40)
    print("[阶段性复盘报告]")
    print("━" * 40)

    if not all_records:
        print("\n[提示] 暂无学习记录")
        print("使用 python cli.py submit 提交记录")
        print("━" * 40)
        return

    start_date, end_date = prompt_date_range()
    records = memory_store.get_records_by_date_range(start_date, end_date)

    if not records:
        print(f"\n[提示] {start_date} ~ {end_date} 期间无学习记录")
        print("━" * 40)
        return

    analyzer = Analyzer(records, config)
    weakness_calc = WeaknessCalculator(records, config)

    print(f"\n" + "━" * 40)
    print(f"[学习复盘] {start_date} ~ {end_date}")
    print(f"━" * 40)

    total_hours = analyzer.calculate_total_hours()
    total_days = len(set(r.date for r in records))
    avg_hours = total_hours / total_days if total_days > 0 else 0

    print(f"\n[学习概况]")
    print(f"  学习天数：{total_days} 天")
    print(f"  总学习时长：{total_hours:.1f} 小时")
    print(f"  平均每日：{avg_hours:.1f} 小时")

    distribution = analyzer.calculate_subject_distribution()
    if distribution:
        print(f"\n[科目分布]")
        for subject, data in distribution.items():
            bar_len = int(data['percentage'] / 5)
            bar = "#" * bar_len + "-" * (20 - bar_len)
            print(f"  {subject:<12} [{bar}] {data['percentage']:.1f}%")

    frequent_problems = analyzer.find_frequent_problems(5)
    if frequent_problems:
        print(f"\n[高频错误]")
        for i, (problem, count) in enumerate(frequent_problems, 1):
            print(f"  {i}. {problem}：{count}次提问")

    weak_points = weakness_calc.identify_weak_points()
    weak_only = [p for p in weak_points if p["level"] == "薄弱"]
    attention = [p for p in weak_points if p["level"] == "关注"]

    if weak_only or attention:
        print(f"\n[薄弱知识点分析]")
        for p in weak_only + attention:
            level_icon = "[薄弱]" if p["level"] == "薄弱" else "[关注]"
            print(f"\n  {level_icon} 【{p['subject']}:{p['chapter']}】 WeaknessScore: {p['score']}")
            print(f"     提问次数：{p['question_count']}  重复学习：{p['repeat_count']}次")
            print(f"     平均理解度：{p['avg_rating']}/5  未复习：{p['days_since']}天")

    forgettable = weakness_calc.get_forgettable_points(config.thresholds.forget_days)
    if forgettable:
        print(f"\n[重复遗忘风险]")
        for p in forgettable:
            print(f"  - {p['subject']}：{p['chapter']} ({p['days_since']}天未复习, {p['level']})")

    print(f"\n[改进建议]")
    if weak_only:
        print(f"  1. 重点复习 {weak_only[0]['subject']}:{weak_only[0]['chapter']}")
    if distribution:
        min_subject = min(distribution.items(), key=lambda x: x[1]['hours'])
        print(f"  2. {min_subject[0]} 学习时间较少，建议加强")
    streak = analyzer.calculate_streak()
    print(f"  3. 当前连续学习 {streak} 天，继续保持！")

    print("━" * 40)
