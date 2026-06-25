from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass
class Record:
    id: str
    date: str
    subject: str
    chapter: str
    duration: float
    content: str
    problems: Optional[str]
    self_rating: int
    ai_summary: Optional[str]
    created_at: str

    def validate(self) -> list[str]:
        errors = []
        if self.duration < 0:
            errors.append("学习时长不能为负数")
        if self.duration > 16:
            errors.append("学习时长超过16小时")
        if self.self_rating < 1 or self.self_rating > 5:
            errors.append("自评分数必须在1-5之间")
        if not self.chapter.strip():
            errors.append("章节不能为空")
        return errors

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "subject": self.subject,
            "chapter": self.chapter,
            "duration": self.duration,
            "content": self.content,
            "problems": self.problems,
            "self_rating": self.self_rating,
            "ai_summary": self.ai_summary,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Record':
        return cls(
            id=data.get("id", ""),
            date=data.get("date", ""),
            subject=data.get("subject", ""),
            chapter=data.get("chapter", ""),
            duration=data.get("duration", 0),
            content=data.get("content", ""),
            problems=data.get("problems"),
            self_rating=data.get("self_rating", 3),
            ai_summary=data.get("ai_summary"),
            created_at=data.get("created_at", "")
        )


def generate_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_suffix = random.randint(100, 999)
    return f"{timestamp}-{random_suffix}"
