from storage.memory_store import MemoryStore
from storage.config_store import ConfigStore
from core.analyzer import Analyzer
from core.weakness import WeaknessCalculator


def execute(args=None):
    memory_store = MemoryStore()
    config_store = ConfigStore()
    config = config_store.load_config()
    records = memory_store.get_all_records()

    print("━" * 40)
    print("[学习进度报告]")
    print("━" * 40)

    if not records:
        print("\n[提示] 暂无学习记录")
        print("使用 python cli.py submit 提交记录")
        print("━" * 40)
        return

    analyzer = Analyzer(records, config)
    weakness_calc = WeaknessCalculator(records, config)

    total_hours = analyzer.calculate_total_hours()
    streak = analyzer.calculate_streak()
    total_records = analyzer.calculate_total_records()

    print(f"\n[总体概览]")
    print(f"  总学习时长：{total_hours:.1f} 小时")
    print(f"  连续学习：{streak} 天")
    print(f"  学习次数：{total_records} 次")

    distribution = analyzer.calculate_subject_distribution()
    if distribution:
        print(f"\n[科目占比]")
        print(f"  ┌{'─'*18}┬{'─'*9}┬{'─'*10}┐")
        print(f"  │ {'科目':<16} │ {'时长':<7} │ {'占比':<8} │")
        print(f"  ├{'─'*18}┼{'─'*9}┼{'─'*10}┤")
        for subject, data in distribution.items():
            print(f"  │ {subject:<16} │ {data['hours']:<7.1f} │ {data['percentage']:<7.1f}% │")
        print(f"  └{'─'*18}┴{'─'*9}┴{'─'*10}┘")

    coverage = analyzer.calculate_chapter_coverage()
    if coverage:
        print(f"\n[章节覆盖率]")
        for subject, data in coverage.items():
            print(f"  {subject}：{data['learned']}/{data['total']} 章节 ({data['rate']:.1f}%)")

    frequent_problems = analyzer.find_frequent_problems()
    if frequent_problems:
        print(f"\n[高频疑问]")
        for i, (problem, count) in enumerate(frequent_problems, 1):
            print(f"  {i}. {problem} ({count}次)")

    weak_points = weakness_calc.identify_weak_points()
    weak_only = [p for p in weak_points if p["level"] == "薄弱"]
    if weak_only:
        print(f"\n[薄弱知识点]")
        print(f"  ┌{'─'*18}┬{'─'*10}┬{'─'*8}┐")
        print(f"  │ {'知识点':<16} │ {'得分':<8} │ {'建议':<6} │")
        print(f"  ├{'─'*18}┼{'─'*10}┼{'─'*8}┤")
        for p in weak_only:
            name = f"{p['subject']}:{p['chapter']}"
            if len(name) > 16:
                name = name[:14] + ".."
            print(f"  │ {name:<16} │ {p['score']:<8.1f} │ {'重点':<6} │")
        print(f"  └{'─'*18}┴{'─'*10}┴{'─'*8}┘")

    forgettable = weakness_calc.get_forgettable_points(config.thresholds.forget_days)
    if forgettable:
        print(f"\n[遗忘风险] (>{config.thresholds.forget_days}天未复习)")
        for p in forgettable:
            print(f"  - {p['subject']}：{p['chapter']} ({p['days_since']}天前)")

    prediction = analyzer.predict_completion()
    if prediction:
        print(f"\n[冲刺预测]")
        print(f"  按当前进度，预计在目标日期前可完成 {prediction['rate']}% 的内容")
        if prediction.get('suggested_hours'):
            print(f"  建议每日学习：{prediction['suggested_hours']} 小时")

    print("━" * 40)
