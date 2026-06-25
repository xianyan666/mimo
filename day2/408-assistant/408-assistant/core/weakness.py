from datetime import date, datetime
from collections import defaultdict
from typing import Optional

from models.record import Record
from models.config import Config, WeaknessWeights


class WeaknessCalculator:
    def __init__(self, records: list[Record], config: Config):
        self.records = records
        self.config = config
        self.weights = config.weakness_weights
        self.threshold = config.thresholds.weakness_score

    def extract_knowledge_points(self) -> dict:
        points = defaultdict(list)
        for r in self.records:
            key = f"{r.subject}:{r.chapter}"
            points[key].append(r)
        return points

    def calculate_question_count(self, records: list[Record]) -> int:
        return sum(1 for r in records if r.problems and r.problems.strip())

    def calculate_repeat_count(self, records: list[Record]) -> int:
        return len(records)

    def calculate_avg_self_rating(self, records: list[Record]) -> float:
        if not records:
            return 3.0
        return sum(r.self_rating for r in records) / len(records)

    def calculate_days_since_review(self, records: list[Record]) -> int:
        if not records:
            return 30
        dates = [r.date for r in records]
        latest = max(dates)
        try:
            latest_date = date.fromisoformat(latest)
            return (date.today() - latest_date).days
        except ValueError:
            return 30

    def calculate_weakness_score(self, records: list[Record]) -> float:
        question_count = self.calculate_question_count(records)
        repeat_count = self.calculate_repeat_count(records)
        avg_rating = self.calculate_avg_self_rating(records)
        days_since = self.calculate_days_since_review(records)

        score = (
            self.weights.question_count * question_count +
            self.weights.repeat_count * repeat_count +
            self.weights.self_rating * (5 - avg_rating) +
            self.weights.days_since_review * days_since
        )

        return round(score, 1)

    def identify_weak_points(self) -> list[dict]:
        points = self.extract_knowledge_points()
        weak_points = []

        for key, records in points.items():
            score = self.calculate_weakness_score(records)
            subject, chapter = key.split(":")

            weak_points.append({
                "subject": subject,
                "chapter": chapter,
                "score": score,
                "question_count": self.calculate_question_count(records),
                "repeat_count": len(records),
                "avg_rating": round(self.calculate_avg_self_rating(records), 1),
                "days_since": self.calculate_days_since_review(records),
                "level": self.classify_weakness_level(score)
            })

        weak_points.sort(key=lambda x: x["score"], reverse=True)
        return weak_points

    def classify_weakness_level(self, score: float) -> str:
        if score >= self.threshold:
            return "薄弱"
        elif score >= 4:
            return "关注"
        else:
            return "良好"

    def get_weak_points_summary(self) -> dict:
        weak_points = self.identify_weak_points()
        weak = [p for p in weak_points if p["level"] == "薄弱"]
        attention = [p for p in weak_points if p["level"] == "关注"]
        good = [p for p in weak_points if p["level"] == "良好"]

        return {
            "weak": weak,
            "attention": attention,
            "good": good,
            "total": len(weak_points)
        }

    def get_forgettable_points(self, forget_days: int = 7) -> list[dict]:
        points = self.extract_knowledge_points()
        forgettable = []

        for key, records in points.items():
            days_since = self.calculate_days_since_review(records)
            if days_since > forget_days:
                subject, chapter = key.split(":")
                forgettable.append({
                    "subject": subject,
                    "chapter": chapter,
                    "days_since": days_since,
                    "level": "低风险" if days_since <= 14 else ("中风险" if days_since <= 30 else "高风险")
                })

        forgettable.sort(key=lambda x: x["days_since"], reverse=True)
        return forgettable
