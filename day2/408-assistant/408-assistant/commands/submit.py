import sys
from datetime import date, datetime

from models.record import Record, generate_id
from core.summary import generate_summary
from storage.memory_store import MemoryStore
from storage.config_store import ConfigStore


SUBJECTS = {
    "1": "数据结构",
    "2": "计算机组成原理",
    "3": "操作系统",
    "4": "计算机网络"
}


def prompt_subject(config_store: ConfigStore) -> str:
    subject_names = config_store.get_subject_names()

    print("\n请选择科目：")
    for i, name in enumerate(subject_names, 1):
        print(f"  {i}. {name}")

    while True:
        choice = input("\n请输入选项 (1-4): ").strip()
        if choice in SUBJECTS:
            return SUBJECTS[choice]
        print("[错误] 请输入1-4的数字")


def prompt_chapter(config_store: ConfigStore, subject: str) -> str:
    chapters = config_store.get_subject_chapters(subject)

    if chapters:
        print(f"\n【{subject}】的章节列表：")
        for i, ch in enumerate(chapters, 1):
            print(f"  {i}. {ch}")
        print("  或直接输入章节名称")

    while True:
        chapter = input("\n请输入章节: ").strip()
        if not chapter:
            print("[错误] 章节不能为空")
            continue
        if chapter.isdigit() and chapters:
            idx = int(chapter) - 1
            if 0 <= idx < len(chapters):
                return chapters[idx]
        return chapter


def prompt_duration() -> float:
    while True:
        try:
            duration = float(input("\n请输入学习时长(小时): ").strip())
            if duration < 0:
                print("[错误] 学习时长不能为负数")
                continue
            if duration > 16:
                confirm = input("[警告] 学习时长超过16小时，确认吗？(y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            return duration
        except ValueError:
            print("[错误] 请输入有效的数字")


def prompt_content() -> str:
    print("\n请输入学习内容（输入空行结束）：")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def prompt_problems() -> str:
    print("\n请输入遇到的问题（输入空行结束，可跳过）：")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines) if lines else ""


def prompt_rating() -> int:
    while True:
        try:
            rating = int(input("\n请评价理解度 (1-5，5为完全理解): ").strip())
            if 1 <= rating <= 5:
                return rating
            print("[错误] 请输入1-5的数字")
        except ValueError:
            print("[错误] 请输入有效的数字")


def execute(args=None):
    config_store = ConfigStore()
    memory_store = MemoryStore()

    print("━" * 40)
    print("[提交学习记录]")
    print("━" * 40)

    subject = prompt_subject(config_store)
    chapter = prompt_chapter(config_store, subject)
    duration = prompt_duration()
    content = prompt_content()
    problems = prompt_problems()
    rating = prompt_rating()

    record = Record(
        id=generate_id(),
        date=date.today().isoformat(),
        subject=subject,
        chapter=chapter,
        duration=duration,
        content=content,
        problems=problems,
        self_rating=rating,
        ai_summary=None,
        created_at=datetime.now().isoformat()
    )

    errors = record.validate()
    if errors:
        for err in errors:
            print(f"[错误] {err}")
        return

    record.ai_summary = generate_summary(record)
    memory_store.save_record(record)

    print("\n[成功] 学习记录已保存")
    print("\n" + "━" * 40)
    print("[AI学习总结]")
    print("━" * 40)
    print(record.ai_summary)
    print("━" * 40)
