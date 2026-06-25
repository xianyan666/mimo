from datetime import date

from storage.memory_store import MemoryStore


def format_rating(rating: int) -> str:
    return "★" * rating + "☆" * (5 - rating)


def execute(args=None):
    memory_store = MemoryStore()
    today = date.today().isoformat()
    records = memory_store.get_today_records()

    print("━" * 40)
    print(f"[今日学习记录] {today}")
    print("━" * 40)

    if not records:
        print("\n[提示] 今日暂无学习记录")
        print("使用 python cli.py submit 提交记录")
        print("━" * 40)
        return

    print()
    print(f"┌{'─'*12}┬{'─'*14}┬{'─'*8}┬{'─'*10}┐")
    print(f"│ {'科目':<10} │ {'章节':<12} │ {'时长':<6} │ {'评价':<8} │")
    print(f"├{'─'*12}┼{'─'*14}┼{'─'*8}┼{'─'*10}┤")

    total_hours = 0
    subject_hours = {}
    problems_list = []

    for r in records:
        total_hours += r.duration
        subject_hours[r.subject] = subject_hours.get(r.subject, 0) + r.duration
        if r.problems and r.problems.strip():
            problems_list.append(r.problems)

        chapter_display = r.chapter[:6] if len(r.chapter) > 6 else r.chapter
        print(f"│ {r.subject:<10} │ {chapter_display:<12} │ {r.duration:<6.1f} │ {format_rating(r.self_rating):<8} │")

    print(f"└{'─'*12}┴{'─'*14}┴{'─'*8}┴{'─'*10}┘")

    print(f"\n[今日统计]")
    print(f"  总学习时长：{total_hours:.1f} 小时")

    if subject_hours:
        dist_parts = []
        for subject, hours in subject_hours.items():
            pct = hours / total_hours * 100 if total_hours > 0 else 0
            dist_parts.append(f"{subject} {pct:.1f}%")
        print(f"  科目分布：{' | '.join(dist_parts)}")

    if problems_list:
        print(f"\n[今日问题]")
        for i, p in enumerate(problems_list, 1):
            print(f"  {i}. {p}")

    print("━" * 40)
