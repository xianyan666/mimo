from datetime import date, timedelta, datetime
from collections import Counter
from typing import Optional

from models.record import Record
from models.config import Config


class Analyzer:
    def __init__(self, records: list[Record], config: Config):
        self.records = records
        self.config = config

    def calculate_total_hours(self) -> float:
        return sum(r.duration for r in self.records)

    def calculate_streak(self) -> int:
        if not self.records:
            return 0

        dates = sorted(set(r.date for r in self.records), reverse=True)
        today = date.today()
        yesterday = today - timedelta(days=1)

        if dates[0] != today.isoformat() and dates[0] != yesterday.isoformat():
            return 0

        streak = 1
        for i in range(1, len(dates)):
            current = date.fromisoformat(dates[i-1])
            prev = date.fromisoformat(dates[i])
            if (current - prev) == timedelta(days=1):
                streak += 1
            else:
                break

        return streak

    def calculate_subject_distribution(self) -> dict:
        if not self.records:
            return {}

        subject_hours = {}
        for r in self.records:
            subject_hours[r.subject] = subject_hours.get(r.subject, 0) + r.duration

        total = sum(subject_hours.values())
        distribution = {}
        for subject, hours in subject_hours.items():
            distribution[subject] = {
                "hours": hours,
                "percentage": (hours / total * 100) if total > 0 else 0
            }

        return distribution

    def calculate_chapter_coverage(self) -> dict:
        coverage = {}
        for subject_config in self.config.subjects:
            subject_name = subject_config.name
            total_chapters = len(subject_config.chapters)
            learned_chapters = set(
                r.chapter for r in self.records
                if r.subject == subject_name
            )
            coverage[subject_name] = {
                "learned": len(learned_chapters),
                "total": total_chapters,
                "rate": (len(learned_chapters) / total_chapters * 100) if total_chapters > 0 else 0,
                "chapters": list(learned_chapters)
            }

        return coverage

    def find_frequent_problems(self, top_n: int = 5) -> list[tuple[str, int]]:
        problems = [r.problems for r in self.records if r.problems and r.problems.strip()]
        if not problems:
            return []

        word_count = Counter()
        for p in problems:
            words = p.replace("，", " ").replace("。", " ").replace("、", " ").split()
            for word in words:
                if len(word) > 1:
                    word_count[word] += 1

        return word_count.most_common(top_n)

    def find_forgettable_content(self, forget_days: int = 7) -> list[dict]:
        today = date.today()
        forgettable = []

        subject_chapter_last_review = {}
        for r in self.records:
            key = f"{r.subject}:{r.chapter}"
            if key not in subject_chapter_last_review:
                subject_chapter_last_review[key] = r.date
            elif r.date > subject_chapter_last_review[key]:
                subject_chapter_last_review[key] = r.date

        for key, last_date_str in subject_chapter_last_review.items():
            last_date = date.fromisoformat(last_date_str)
            days_since = (today - last_date).days
            if days_since > forget_days:
                subject, chapter = key.split(":")
                forgettable.append({
                    "subject": subject,
                    "chapter": chapter,
                    "days_since": days_since,
                    "last_review": last_date_str
                })

        forgettable.sort(key=lambda x: x["days_since"], reverse=True)
        return forgettable

    def calculate_total_study_days(self) -> int:
        return len(set(r.date for r in self.records))

    def calculate_total_records(self) -> int:
        return len(self.records)

    def get_recent_records(self, days: int = 7) -> list[Record]:
        today = date.today()
        start_date = (today - timedelta(days=days)).isoformat()
        return [r for r in self.records if r.date >= start_date]

    def predict_completion(self) -> dict:
        if not self.records:
            return {"rate": 0, "suggested_hours": 0}

        total_hours = self.calculate_total_hours()
        total_days = self.calculate_study_days()
        streak = self.calculate_streak()

        if total_days == 0:
            return {"rate": 0, "suggested_hours": self.config.user.daily_goal_hours}

        avg_hours_per_day = total_hours / total_days

        try:
            target_date = date.fromisoformat(self.config.user.target_date)
            days_remaining = (target_date - date.today()).days
        except ValueError:
            days_remaining = 180

        if days_remaining <= 0:
            return {"rate": 100, "suggested_hours": 0}

        total_subjects = len(self.config.subjects)
        total_chapters = sum(len(s.chapters) for s in self.config.subjects)
        coverage = self.calculate_chapter_coverage()
        learned_chapters = sum(c["learned"] for c in coverage.values())
        current_progress = (learned_chapters / total_chapters * 100) if total_chapters > 0 else 0

        efficiency = 0.8 if streak <= 7 else (0.9 if streak <= 14 else 1.0)
        predicted_rate = min(100, (current_progress / max(1, total_days)) * days_remaining * efficiency)

        total_remaining_hours = (100 - current_progress) / 100 * total_hours * (total_chapters / max(1, learned_chapters))
        suggested_hours = total_remaining_hours / max(1, days_remaining)

        return {
            "rate": round(predicted_rate, 1),
            "suggested_hours": round(max(suggested_hours, 2), 1),
            "days_remaining": days_remaining,
            "current_progress": round(current_progress, 1)
        }

    def calculate_study_days(self) -> int:
        return len(set(r.date for r in self.records))
