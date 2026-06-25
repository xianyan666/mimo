from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubjectConfig:
    name: str
    chapters: list[str]


@dataclass
class UserConfig:
    name: str = "考生"
    target_date: str = "2025-12-21"
    daily_goal_hours: float = 4.0


@dataclass
class WeaknessWeights:
    question_count: float = 2.0
    repeat_count: float = 1.5
    self_rating: float = 1.0
    days_since_review: float = 0.5


@dataclass
class Thresholds:
    weakness_score: float = 8.0
    forget_days: int = 7
    max_daily_hours: float = 16.0


@dataclass
class Config:
    user: UserConfig = field(default_factory=UserConfig)
    subjects: list[SubjectConfig] = field(default_factory=list)
    weakness_weights: WeaknessWeights = field(default_factory=WeaknessWeights)
    thresholds: Thresholds = field(default_factory=Thresholds)

    def to_dict(self) -> dict:
        return {
            "user": {
                "name": self.user.name,
                "target_date": self.user.target_date,
                "daily_goal_hours": self.user.daily_goal_hours
            },
            "subjects": [
                {"name": s.name, "chapters": s.chapters}
                for s in self.subjects
            ],
            "weakness_weights": {
                "question_count": self.weakness_weights.question_count,
                "repeat_count": self.weakness_weights.repeat_count,
                "self_rating": self.weakness_weights.self_rating,
                "days_since_review": self.weakness_weights.days_since_review
            },
            "thresholds": {
                "weakness_score": self.thresholds.weakness_score,
                "forget_days": self.thresholds.forget_days,
                "max_daily_hours": self.thresholds.max_daily_hours
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        user_data = data.get("user", {})
        user = UserConfig(
            name=user_data.get("name", "考生"),
            target_date=user_data.get("target_date", "2025-12-21"),
            daily_goal_hours=user_data.get("daily_goal_hours", 4.0)
        )

        subjects = []
        for s in data.get("subjects", []):
            subjects.append(SubjectConfig(
                name=s.get("name", ""),
                chapters=s.get("chapters", [])
            ))

        weights_data = data.get("weakness_weights", {})
        weakness_weights = WeaknessWeights(
            question_count=weights_data.get("question_count", 2.0),
            repeat_count=weights_data.get("repeat_count", 1.5),
            self_rating=weights_data.get("self_rating", 1.0),
            days_since_review=weights_data.get("days_since_review", 0.5)
        )

        thresholds_data = data.get("thresholds", {})
        thresholds = Thresholds(
            weakness_score=thresholds_data.get("weakness_score", 8.0),
            forget_days=thresholds_data.get("forget_days", 7),
            max_daily_hours=thresholds_data.get("max_daily_hours", 16.0)
        )

        return cls(
            user=user,
            subjects=subjects,
            weakness_weights=weakness_weights,
            thresholds=thresholds
        )


def get_default_config() -> Config:
    subjects = [
        SubjectConfig(
            name="数据结构",
            chapters=["线性表", "栈和队列", "树与二叉树", "图", "查找", "排序"]
        ),
        SubjectConfig(
            name="计算机组成原理",
            chapters=["数据的表示和运算", "存储器层次结构", "指令系统", "中央处理器", "总线", "输入/输出系统"]
        ),
        SubjectConfig(
            name="操作系统",
            chapters=["进程管理", "内存管理", "文件管理", "输入/输出管理"]
        ),
        SubjectConfig(
            name="计算机网络",
            chapters=["物理层", "数据链路层", "网络层", "传输层", "应用层"]
        )
    ]

    return Config(
        user=UserConfig(),
        subjects=subjects,
        weakness_weights=WeaknessWeights(),
        thresholds=Thresholds()
    )
