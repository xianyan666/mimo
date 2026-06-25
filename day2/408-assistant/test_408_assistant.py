import pytest
import os
import sys
import json
import tempfile
import shutil
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "408-assistant"))

from models.record import Record, generate_id
from models.config import Config, UserConfig, SubjectConfig, WeaknessWeights, Thresholds, get_default_config
from core.weakness import WeaknessCalculator
from core.analyzer import Analyzer
from core.summary import generate_summary
from storage.memory_store import MemoryStore
from storage.config_store import ConfigStore


@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config():
    return get_default_config()


@pytest.fixture
def sample_record():
    return Record(
        id="20240115143000-123",
        date=date.today().isoformat(),
        subject="数据结构",
        chapter="线性表",
        duration=2.5,
        content="学习了单链表基本操作",
        problems="头插法和尾插法区别",
        self_rating=3,
        ai_summary=None,
        created_at=datetime.now().isoformat()
    )


@pytest.fixture
def sample_records():
    today = date.today()
    return [
        Record(
            id=f"id-{i}",
            date=(today - timedelta(days=i)).isoformat(),
            subject="数据结构",
            chapter="线性表",
            duration=float(i + 1),
            content=f"内容{i}",
            problems="问题" if i % 2 == 0 else "",
            self_rating=3,
            ai_summary=None,
            created_at=datetime.now().isoformat()
        )
        for i in range(5)
    ]


class TestRecordModel:
    def test_validate_normal(self, sample_record):
        assert sample_record.validate() == []

    def test_validate_negative_duration(self, sample_record):
        sample_record.duration = -1
        errors = sample_record.validate()
        assert "学习时长不能为负数" in errors

    def test_validate_zero_duration(self, sample_record):
        sample_record.duration = 0
        assert sample_record.validate() == []

    def test_validate_exceed_16_hours(self, sample_record):
        sample_record.duration = 17
        errors = sample_record.validate()
        assert "学习时长超过16小时" in errors

    def test_validate_exactly_16_hours(self, sample_record):
        sample_record.duration = 16
        assert sample_record.validate() == []

    def test_validate_rating_below_1(self, sample_record):
        sample_record.self_rating = 0
        errors = sample_record.validate()
        assert "自评分数必须在1-5之间" in errors

    def test_validate_rating_above_5(self, sample_record):
        sample_record.self_rating = 6
        errors = sample_record.validate()
        assert "自评分数必须在1-5之间" in errors

    def test_validate_rating_1(self, sample_record):
        sample_record.self_rating = 1
        assert sample_record.validate() == []

    def test_validate_rating_5(self, sample_record):
        sample_record.self_rating = 5
        assert sample_record.validate() == []

    def test_validate_empty_chapter(self, sample_record):
        sample_record.chapter = ""
        errors = sample_record.validate()
        assert "章节不能为空" in errors

    def test_to_dict(self, sample_record):
        d = sample_record.to_dict()
        assert d["id"] == sample_record.id
        assert d["subject"] == sample_record.subject
        assert d["duration"] == sample_record.duration

    def test_from_dict(self, sample_record):
        d = sample_record.to_dict()
        restored = Record.from_dict(d)
        assert restored.id == sample_record.id
        assert restored.subject == sample_record.subject

    def test_generate_id_unique(self):
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2

    def test_generate_id_format(self):
        rid = generate_id()
        parts = rid.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 14
        assert len(parts[1]) == 3


class TestWeaknessCalculator:
    def test_score_basic(self, sample_config):
        records = [
            Record("1", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "问题", 2, None, ""),
            Record("2", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "问题", 2, None, ""),
            Record("3", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "", 2, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        with patch("core.weakness.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 25)
            mock_date.fromisoformat = date.fromisoformat
            score = calc.calculate_weakness_score(records)
        assert score > 0

    def test_score_no_questions(self, sample_config):
        records = [
            Record("1", date.today().isoformat(), "数据结构", "线性表", 2.0, "内容", "", 4, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        score = calc.calculate_weakness_score(records)
        assert score < 8

    def test_score_high_rating(self, sample_config):
        records = [
            Record("1", date.today().isoformat(), "数据结构", "线性表", 2.0, "内容", "", 5, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        score = calc.calculate_weakness_score(records)
        assert score == round(1.5 * 1 + 1.0 * 0 + 0.5 * 0, 1)

    def test_level_good(self, sample_config):
        calc = WeaknessCalculator([], sample_config)
        assert calc.classify_weakness_level(3.5) == "良好"

    def test_level_attention(self, sample_config):
        calc = WeaknessCalculator([], sample_config)
        assert calc.classify_weakness_level(6.0) == "关注"

    def test_level_weak(self, sample_config):
        calc = WeaknessCalculator([], sample_config)
        assert calc.classify_weakness_level(10.0) == "薄弱"

    def test_level_boundary_4(self, sample_config):
        calc = WeaknessCalculator([], sample_config)
        assert calc.classify_weakness_level(4.0) == "关注"

    def test_level_boundary_8(self, sample_config):
        calc = WeaknessCalculator([], sample_config)
        assert calc.classify_weakness_level(8.0) == "薄弱"

    def test_question_count(self, sample_config):
        records = [
            Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "问题1", 3, None, ""),
            Record("2", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("3", "2024-01-15", "DS", "线性表", 2.0, "内容", "问题2", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        assert calc.calculate_question_count(records) == 2

    def test_repeat_count(self, sample_config):
        records = [
            Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", "2024-01-16", "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        assert calc.calculate_repeat_count(records) == 2

    def test_avg_self_rating(self, sample_config):
        records = [
            Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 2, None, ""),
            Record("2", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 4, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        assert calc.calculate_avg_self_rating(records) == 3.0

    def test_forgettable_low_risk(self, sample_config):
        records = [
            Record("1", (date.today() - timedelta(days=10)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        result = calc.get_forgettable_points(7)
        assert len(result) == 1
        assert result[0]["level"] == "低风险"

    def test_forgettable_medium_risk(self, sample_config):
        records = [
            Record("1", (date.today() - timedelta(days=20)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        result = calc.get_forgettable_points(7)
        assert result[0]["level"] == "中风险"

    def test_forgettable_high_risk(self, sample_config):
        records = [
            Record("1", (date.today() - timedelta(days=35)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        result = calc.get_forgettable_points(7)
        assert result[0]["level"] == "高风险"

    def test_no_forgettable_within_7_days(self, sample_config):
        records = [
            Record("1", (date.today() - timedelta(days=5)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        result = calc.get_forgettable_points(7)
        assert len(result) == 0

    def test_forgettable_boundary_8_days(self, sample_config):
        records = [
            Record("1", (date.today() - timedelta(days=8)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        calc = WeaknessCalculator(records, sample_config)
        result = calc.get_forgettable_points(7)
        assert len(result) == 1


class TestAnalyzer:
    def test_total_hours(self, sample_config, sample_records):
        analyzer = Analyzer(sample_records, sample_config)
        assert analyzer.calculate_total_hours() == sum(r.duration for r in sample_records)

    def test_streak_continuous(self, sample_config):
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=1)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("3", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        analyzer = Analyzer(records, sample_config)
        assert analyzer.calculate_streak() == 3

    def test_streak_broken(self, sample_config):
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        analyzer = Analyzer(records, sample_config)
        assert analyzer.calculate_streak() == 1

    def test_streak_from_yesterday(self, sample_config):
        today = date.today()
        records = [
            Record("1", (today - timedelta(days=1)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        analyzer = Analyzer(records, sample_config)
        assert analyzer.calculate_streak() == 2

    def test_streak_empty(self, sample_config):
        analyzer = Analyzer([], sample_config)
        assert analyzer.calculate_streak() == 0

    def test_subject_distribution(self, sample_config):
        records = [
            Record("1", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", "2024-01-15", "操作系统", "进程管理", 2.0, "内容", "", 3, None, ""),
        ]
        analyzer = Analyzer(records, sample_config)
        dist = analyzer.calculate_subject_distribution()
        assert "数据结构" in dist
        assert "操作系统" in dist
        assert dist["数据结构"]["percentage"] == 50.0

    def test_chapter_coverage(self, sample_config):
        records = [
            Record("1", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", "2024-01-15", "数据结构", "栈和队列", 2.0, "内容", "", 3, None, ""),
        ]
        analyzer = Analyzer(records, sample_config)
        coverage = analyzer.calculate_chapter_coverage()
        assert coverage["数据结构"]["learned"] == 2
        assert coverage["数据结构"]["total"] == 6

    def test_find_frequent_problems(self, sample_config):
        records = [
            Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "快速排序问题", 3, None, ""),
            Record("2", "2024-01-15", "DS", "线性表", 2.0, "内容", "快速排序", 3, None, ""),
            Record("3", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        analyzer = Analyzer(records, sample_config)
        problems = analyzer.find_frequent_problems()
        assert len(problems) > 0

    def test_total_records(self, sample_config, sample_records):
        analyzer = Analyzer(sample_records, sample_config)
        assert analyzer.calculate_total_records() == 5

    def test_total_study_days(self, sample_config, sample_records):
        analyzer = Analyzer(sample_records, sample_config)
        assert analyzer.calculate_total_study_days() == 5

    def test_predict_completion(self, sample_config):
        today = date.today()
        records = [
            Record("1", today.isoformat(), "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        config = Config(
            user=UserConfig(target_date=(today + timedelta(days=180)).isoformat()),
            subjects=sample_config.subjects,
            weakness_weights=sample_config.weakness_weights,
            thresholds=sample_config.thresholds
        )
        analyzer = Analyzer(records, config)
        prediction = analyzer.predict_completion()
        assert "rate" in prediction
        assert "suggested_hours" in prediction


class TestSummary:
    def test_excellent_template(self):
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "", 5, None, "")
        summary = generate_summary(record)
        assert "理解度很高" in summary
        assert "数据结构" in summary
        assert "线性表" in summary

    def test_good_template(self):
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "", 4, None, "")
        summary = generate_summary(record)
        assert "理解度良好" in summary

    def test_normal_template_with_problems(self):
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "问题", 3, None, "")
        summary = generate_summary(record)
        assert "理解度一般" in summary

    def test_no_problems_template(self):
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "", 3, None, "")
        summary = generate_summary(record)
        assert "学习过程顺利" in summary

    def test_weak_template(self):
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "难点", 2, None, "")
        summary = generate_summary(record)
        assert "理解度较低" in summary

    def test_weak_no_problems(self):
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "", 2, None, "")
        summary = generate_summary(record)
        assert "理解度一般" in summary

    def test_summary_contains_subject(self):
        record = Record("1", "2024-01-15", "计算机网络", "传输层", 2.0, "内容", "", 3, None, "")
        summary = generate_summary(record)
        assert "计算机网络" in summary

    def test_summary_contains_chapter(self):
        record = Record("1", "2024-01-15", "操作系统", "进程管理", 2.0, "内容", "", 3, None, "")
        summary = generate_summary(record)
        assert "进程管理" in summary

    def test_summary_contains_duration(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 3.5, "内容", "", 3, None, "")
        summary = generate_summary(record)
        assert "3.5" in summary

    def test_summary_contains_rating(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 4, None, "")
        summary = generate_summary(record)
        assert "4/5" in summary

    def test_summary_problems_none(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", None, 3, None, "")
        summary = generate_summary(record)
        assert "学习过程顺利" in summary or "理解度一般" in summary

    def test_summary_problems_empty(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, "")
        summary = generate_summary(record)
        assert "无" in summary or "顺利" in summary


class TestMemoryStore:
    def test_save_and_get(self, temp_data_dir, sample_record):
        store = MemoryStore(temp_data_dir)
        store.save_record(sample_record)
        records = store.get_all_records()
        assert len(records) == 1
        assert records[0].id == sample_record.id

    def test_get_today_records(self, temp_data_dir, sample_record):
        store = MemoryStore(temp_data_dir)
        store.save_record(sample_record)
        today_records = store.get_today_records()
        assert len(today_records) == 1

    def test_get_records_by_date(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, "")
        store.save_record(record)
        records = store.get_records_by_date("2024-01-15")
        assert len(records) == 1

    def test_get_records_by_subject(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        record = Record("1", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "", 3, None, "")
        store.save_record(record)
        records = store.get_records_by_subject("数据结构")
        assert len(records) == 1

    def test_has_records(self, temp_data_dir, sample_record):
        store = MemoryStore(temp_data_dir)
        assert not store.has_records()
        store.save_record(sample_record)
        assert store.has_records()

    def test_unique_dates(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        store.save_record(Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", "2024-01-16", "DS", "线性表", 2.0, "内容", "", 3, None, ""))
        dates = store.get_unique_dates()
        assert len(dates) == 2

    def test_unique_subjects(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        store.save_record(Record("1", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", "2024-01-15", "操作系统", "进程管理", 2.0, "内容", "", 3, None, ""))
        subjects = store.get_unique_subjects()
        assert len(subjects) == 2

    def test_multiple_records_same_day(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        store.save_record(Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", "2024-01-15", "DS", "栈和队列", 2.0, "内容", "", 3, None, ""))
        records = store.get_records_by_date("2024-01-15")
        assert len(records) == 2

    def test_date_range_query(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        store.save_record(Record("1", "2024-01-10", "DS", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("3", "2024-01-20", "DS", "线性表", 2.0, "内容", "", 3, None, ""))
        records = store.get_records_by_date_range("2024-01-12", "2024-01-18")
        assert len(records) == 1

    def test_metadata_updated(self, temp_data_dir, sample_record):
        store = MemoryStore(temp_data_dir)
        store.save_record(sample_record)
        data = store._load()
        assert "last_updated" in data["metadata"]


class TestConfigStore:
    def test_default_config(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        config = store.load_config()
        assert config.user.name == "考生"
        assert len(config.subjects) == 4

    def test_subject_names(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        names = store.get_subject_names()
        assert "数据结构" in names
        assert "计算机组成原理" in names

    def test_subject_chapters(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        chapters = store.get_subject_chapters("数据结构")
        assert "线性表" in chapters
        assert "栈和队列" in chapters

    def test_set_user_name(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("user.name", "张三")
        assert result is True
        config = store.load_config()
        assert config.user.name == "张三"

    def test_set_target_date(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("user.target_date", "2025-12-21")
        assert result is True

    def test_set_daily_goal_hours(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("user.daily_goal_hours", "6")
        assert result is True
        config = store.load_config()
        assert config.user.daily_goal_hours == 6.0

    def test_set_invalid_key(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("user.invalid", "value")
        assert result is False

    def test_set_threshold_weakness_score(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("thresholds.weakness_score", "10")
        assert result is True

    def test_set_threshold_forget_days(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("thresholds.forget_days", "14")
        assert result is True

    def test_set_invalid_section(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("invalid.field", "value")
        assert result is False


class TestSubmitCommand:
    @patch("builtins.input", side_effect=["1", "线性表", "2.5", "学习内容", "", "", "3"])
    def test_submit_normal(self, mock_input, temp_data_dir):
        from commands.submit import execute
        with patch("commands.submit.ConfigStore") as MockConfig, \
             patch("commands.submit.MemoryStore") as MockMemory:
            mock_config = MagicMock()
            mock_config.get_subject_names.return_value = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
            mock_config.get_subject_chapters.return_value = ["线性表", "栈和队列"]
            MockConfig.return_value = mock_config
            
            mock_memory = MagicMock()
            MockMemory.return_value = mock_memory
            
            args = MagicMock()
            execute(args)
            mock_memory.save_record.assert_called_once()

    @patch("builtins.input", side_effect=["5"])
    def test_invalid_subject(self, mock_input):
        from commands.submit import prompt_subject
        mock_config = MagicMock()
        mock_config.get_subject_names.return_value = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
        
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(StopIteration):
                prompt_subject(mock_config)

    @patch("builtins.input", side_effect=["abc"])
    def test_invalid_duration(self, mock_input):
        from commands.submit import prompt_duration
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(StopIteration):
                prompt_duration()

    @patch("builtins.input", side_effect=["-1", "2"])
    def test_negative_duration_then_valid(self, mock_input):
        from commands.submit import prompt_duration
        with patch("sys.stdout", new_callable=StringIO):
            result = prompt_duration()
            assert result == 2.0

    @patch("builtins.input", side_effect=["18", "y"])
    def test_over_16_hours_confirm(self, mock_input):
        from commands.submit import prompt_duration
        with patch("sys.stdout", new_callable=StringIO):
            result = prompt_duration()
            assert result == 18.0

    @patch("builtins.input", side_effect=["18", "n", "5"])
    def test_over_16_hours_cancel(self, mock_input):
        from commands.submit import prompt_duration
        with patch("sys.stdout", new_callable=StringIO):
            result = prompt_duration()
            assert result == 5.0

    @patch("builtins.input", side_effect=["6"])
    def test_invalid_rating(self, mock_input):
        from commands.submit import prompt_rating
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(StopIteration):
                prompt_rating()

    @patch("builtins.input", side_effect=["1"])
    def test_rating_1(self, mock_input):
        from commands.submit import prompt_rating
        with patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 1

    @patch("builtins.input", side_effect=["5"])
    def test_rating_5(self, mock_input):
        from commands.submit import prompt_rating
        with patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 5

    @patch("builtins.input", side_effect=[""])
    def test_empty_chapter(self, mock_input):
        from commands.submit import prompt_chapter
        mock_config = MagicMock()
        mock_config.get_subject_chapters.return_value = ["线性表"]
        
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(StopIteration):
                prompt_chapter(mock_config, "数据结构")


class TestTodayCommand:
    def test_today_with_records(self, temp_data_dir, sample_record):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        store.save_record(sample_record)
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "今日学习记录" in output

    def test_today_no_records(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "暂无学习记录" in output

    def test_today_multiple_records(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", today, "操作系统", "进程管理", 1.5, "内容", "", 4, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "3.5" in output or "3.0" in output

    def test_today_rating_display(self, temp_data_dir):
        from commands.today import format_rating
        assert format_rating(3) == "★★★☆☆"
        assert format_rating(5) == "★★★★★"
        assert format_rating(1) == "★☆☆☆☆"


class TestCheckCommand:
    def test_check_no_records(self, temp_data_dir):
        from commands.check import execute
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = []
            MockMemory.return_value = mock_memory
            
            execute()
            output = mock_stdout.getvalue()
            assert "暂无学习记录" in output

    def test_check_with_records(self, temp_data_dir, sample_records, sample_config):
        from commands.check import execute
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = sample_records
            MockMemory.return_value = mock_memory
            
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "学习进度报告" in output
            assert "总学习时长" in output


class TestReviewCommand:
    @patch("builtins.input", side_effect=["1"])
    def test_review_7_days(self, mock_input, sample_records, sample_config):
        from commands.review import execute
        with patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = sample_records
            mock_memory.get_records_by_date_range.return_value = sample_records
            MockMemory.return_value = mock_memory
            
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "阶段性复盘报告" in output

    @patch("builtins.input", side_effect=["4", "2024-01-01", "2024-01-31"])
    def test_review_custom_range(self, mock_input, sample_records, sample_config):
        from commands.review import execute
        with patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = sample_records
            mock_memory.get_records_by_date_range.return_value = sample_records
            MockMemory.return_value = mock_memory
            
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "学习复盘" in output

    def test_review_no_records(self):
        from commands.review import execute
        with patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = []
            MockMemory.return_value = mock_memory
            
            execute()
            output = mock_stdout.getvalue()
            assert "暂无学习记录" in output

    @patch("builtins.input", side_effect=["1"])
    def test_review_empty_range(self, mock_input, sample_config):
        from commands.review import execute
        with patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = [Record("1", "2024-01-01", "DS", "线性表", 2.0, "", "", 3, None, "")]
            mock_memory.get_records_by_date_range.return_value = []
            MockMemory.return_value = mock_memory
            
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "无学习记录" in output


class TestEdgeCases:
    def test_record_with_none_problems(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", None, 3, None, "")
        assert record.validate() == []

    def test_record_with_empty_problems(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, "")
        assert record.validate() == []

    def test_config_from_dict_missing_fields(self):
        data = {"user": {}}
        config = Config.from_dict(data)
        assert config.user.name == "考生"

    def test_record_from_dict_missing_fields(self):
        data = {}
        record = Record.from_dict(data)
        assert record.id == ""
        assert record.duration == 0

    def test_weakness_with_empty_records(self, sample_config):
        calc = WeaknessCalculator([], sample_config)
        points = calc.identify_weak_points()
        assert len(points) == 0

    def test_analyzer_empty_records(self, sample_config):
        analyzer = Analyzer([], sample_config)
        assert analyzer.calculate_total_hours() == 0
        assert analyzer.calculate_streak() == 0
        assert analyzer.calculate_subject_distribution() == {}

    def test_special_characters_in_content(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "<script>alert('test')</script>", "", 3, None, "")
        assert record.validate() == []

    def test_long_content(self):
        long_content = "a" * 10000
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, long_content, "", 3, None, "")
        assert record.validate() == []

    def test_zero_duration_record(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 0.0, "内容", "", 3, None, "")
        assert record.validate() == []

    def test_max_rating_record(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 5, None, "")
        assert record.validate() == []

    def test_min_rating_record(self):
        record = Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 1, None, "")
        assert record.validate() == []


class TestTodayCommandExtended:
    def test_today_total_hours(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 1.5, "内容", "", 3, None, ""))
        store.save_record(Record("2", today, "操作系统", "进程管理", 2.0, "内容", "", 4, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "3.5" in output

    def test_today_subject_distribution(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", today, "操作系统", "进程管理", 2.0, "内容", "", 3, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "50.0%" in output

    def test_today_problems_display(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "头插法区别", 3, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "今日问题" in output
            assert "头插法区别" in output

    def test_today_no_problems(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 3, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "今日问题" not in output

    def test_today_rating_5_stars(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 5, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "★★★★★" in output

    def test_today_rating_1_star(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 1, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "★☆☆☆☆" in output

    def test_today_chapter_truncate(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "数据的表示和运算", 2.0, "内容", "", 3, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "数据的表示" in output

    def test_today_table_format(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 3, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "┌" in output
            assert "└" in output

    def test_today_separator_lines(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "━" in output

    def test_today_date_display(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today_str = date.today().isoformat()
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert today_str in output

    def test_today_single_subject_100_percent(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "", 3, None, ""))
        store.save_record(Record("2", today, "数据结构", "栈和队列", 1.0, "内容", "", 3, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "100.0%" in output

    def test_today_multiple_problems(self, temp_data_dir):
        from commands.today import execute
        store = MemoryStore(temp_data_dir)
        today = date.today().isoformat()
        store.save_record(Record("1", today, "数据结构", "线性表", 2.0, "内容", "问题1", 3, None, ""))
        store.save_record(Record("2", today, "操作系统", "进程管理", 1.5, "内容", "问题2", 4, None, ""))
        
        with patch("commands.today.MemoryStore", return_value=store), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            execute()
            output = mock_stdout.getvalue()
            assert "1. 问题1" in output
            assert "2. 问题2" in output


class TestCheckCommandExtended:
    def test_check_total_hours(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [
            Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", "2024-01-16", "DS", "线性表", 3.0, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "5.0" in output

    def test_check_streak_3_days(self, temp_data_dir, sample_config):
        from commands.check import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=1)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("3", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "连续学习：3 天" in output or "连续学习：3天" in output

    def test_check_streak_broken(self, temp_data_dir, sample_config):
        from commands.check import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "连续学习：1 天" in output or "连续学习：1天" in output

    def test_check_total_records(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [Record(str(i), "2024-01-15", "DS", "线性表", 2.0, "内容", "", 3, None, "") for i in range(10)]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "学习次数：10 次" in output or "学习次数：10次" in output

    def test_check_subject_distribution(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [
            Record("1", "2024-01-15", "数据结构", "线性表", 6.0, "内容", "", 3, None, ""),
            Record("2", "2024-01-15", "操作系统", "进程管理", 4.0, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "60.0" in output
            assert "40.0" in output

    def test_check_chapter_coverage(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [
            Record("1", "2024-01-15", "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", "2024-01-15", "数据结构", "栈和队列", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "2/6" in output or "2 / 6" in output

    def test_check_frequent_problems(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [
            Record("1", "2024-01-15", "DS", "线性表", 2.0, "内容", "快速排序问题", 3, None, ""),
            Record("2", "2024-01-16", "DS", "线性表", 2.0, "内容", "快速排序", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "高频疑问" in output

    def test_check_weak_points(self, temp_data_dir, sample_config):
        from commands.check import execute
        today = date.today()
        records = [
            Record("1", (today - timedelta(days=10)).isoformat(), "数据结构", "线性表", 2.0, "内容", "问题", 1, None, ""),
        ] * 3
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "薄弱知识点" in output

    def test_check_forget_risk(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [
            Record("1", (date.today() - timedelta(days=10)).isoformat(), "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "遗忘风险" in output

    def test_check_prediction(self, temp_data_dir, sample_config):
        from commands.check import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        config = Config(
            user=UserConfig(target_date=(today + timedelta(days=180)).isoformat()),
            subjects=sample_config.subjects,
            weakness_weights=sample_config.weakness_weights,
            thresholds=sample_config.thresholds
        )
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "冲刺预测" in output

    def test_check_separator_lines(self, temp_data_dir, sample_config):
        from commands.check import execute
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = []
            MockMemory.return_value = mock_memory
            
            execute()
            output = mock_stdout.getvalue()
            assert "━" in output

    def test_check_four_subjects_equal(self, temp_data_dir, sample_config):
        from commands.check import execute
        records = [
            Record("1", "2024-01-15", "数据结构", "线性表", 2.5, "内容", "", 3, None, ""),
            Record("2", "2024-01-15", "计算机组成原理", "存储器", 2.5, "内容", "", 3, None, ""),
            Record("3", "2024-01-15", "操作系统", "进程管理", 2.5, "内容", "", 3, None, ""),
            Record("4", "2024-01-15", "计算机网络", "传输层", 2.5, "内容", "", 3, None, ""),
        ]
        with patch("commands.check.MemoryStore") as MockMemory, \
             patch("commands.check.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "25.0%" in output


class TestReviewCommandExtended:
    @patch("builtins.input", side_effect=["2"])
    def test_review_14_days(self, mock_input, sample_records, sample_config):
        from commands.review import execute
        with patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = sample_records
            mock_memory.get_records_by_date_range.return_value = sample_records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "阶段性复盘报告" in output

    @patch("builtins.input", side_effect=["3"])
    def test_review_30_days(self, mock_input, sample_records, sample_config):
        from commands.review import execute
        with patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = sample_records
            mock_memory.get_records_by_date_range.return_value = sample_records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "阶段性复盘报告" in output

    def test_review_study_days(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=1)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("3", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "学习天数" in output

    def test_review_total_hours(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.5, "内容", "", 3, None, ""),
            Record("2", today.isoformat(), "OS", "进程管理", 1.5, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "4.0" in output

    def test_review_avg_daily_hours(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=1)).isoformat(), "DS", "线性表", 4.0, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "平均每日" in output

    def test_review_subject_distribution_bar(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "数据结构", "线性表", 6.0, "内容", "", 3, None, ""),
            Record("2", today.isoformat(), "操作系统", "进程管理", 4.0, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "科目分布" in output
            assert "60.0%" in output

    def test_review_frequent_errors(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "快速排序", 3, None, ""),
            Record("2", today.isoformat(), "DS", "线性表", 2.0, "内容", "快速排序", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "高频错误" in output

    def test_review_weak_analysis(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", (today - timedelta(days=10)).isoformat(), "数据结构", "线性表", 2.0, "内容", "问题", 1, None, ""),
        ] * 3
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "薄弱知识点分析" in output

    def test_review_forget_risk(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", (today - timedelta(days=10)).isoformat(), "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "遗忘风险" in output

    def test_review_improvement_suggestions(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "数据结构", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", today.isoformat(), "操作系统", "进程管理", 1.0, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "改进建议" in output

    def test_review_streak_encouragement(self, temp_data_dir, sample_config):
        from commands.review import execute
        today = date.today()
        records = [
            Record("1", today.isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("2", (today - timedelta(days=1)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
            Record("3", (today - timedelta(days=2)).isoformat(), "DS", "线性表", 2.0, "内容", "", 3, None, ""),
        ]
        with patch("builtins.input", side_effect=["1"]), \
             patch("commands.review.MemoryStore") as MockMemory, \
             patch("commands.review.ConfigStore") as MockConfig, \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mock_memory = MagicMock()
            mock_memory.get_all_records.return_value = records
            mock_memory.get_records_by_date_range.return_value = records
            MockMemory.return_value = mock_memory
            mock_config = MagicMock()
            mock_config.load_config.return_value = sample_config
            MockConfig.return_value = mock_config
            
            execute()
            output = mock_stdout.getvalue()
            assert "继续保持" in output

    @patch("builtins.input", side_effect=["5"])
    def test_review_invalid_choice(self, mock_input):
        from commands.review import prompt_date_range
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(StopIteration):
                prompt_date_range()

    @patch("builtins.input", side_effect=["4", "invalid-date", "2024-01-01", "2024-01-31"])
    def test_review_invalid_start_date(self, mock_input):
        from commands.review import prompt_date_range
        with patch("sys.stdout", new_callable=StringIO):
            start, end = prompt_date_range()
            assert start == "2024-01-01"


class TestExceptionHandlingExtended:
    def test_empty_input_subject(self):
        from commands.submit import prompt_subject
        mock_config = MagicMock()
        mock_config.get_subject_names.return_value = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
        
        with patch("builtins.input", side_effect=["", "1"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_subject(mock_config)
            assert result == "数据结构"

    def test_empty_input_chapter(self):
        from commands.submit import prompt_chapter
        mock_config = MagicMock()
        mock_config.get_subject_chapters.return_value = ["线性表", "栈和队列"]
        
        with patch("builtins.input", side_effect=["", "线性表"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_chapter(mock_config, "数据结构")
            assert result == "线性表"

    def test_non_numeric_duration(self):
        from commands.submit import prompt_duration
        with patch("builtins.input", side_effect=["abc", "2.5"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_duration()
            assert result == 2.5

    def test_non_numeric_rating(self):
        from commands.submit import prompt_rating
        with patch("builtins.input", side_effect=["xyz", "3"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 3

    def test_decimal_rating(self):
        from commands.submit import prompt_rating
        with patch("builtins.input", side_effect=["3.5", "3"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 3

    def test_negative_rating(self):
        from commands.submit import prompt_rating
        with patch("builtins.input", side_effect=["-1", "3"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 3

    def test_rating_above_5(self):
        from commands.submit import prompt_rating
        with patch("builtins.input", side_effect=["10", "5"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 5

    def test_rating_zero(self):
        from commands.submit import prompt_rating
        with patch("builtins.input", side_effect=["0", "3"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_rating()
            assert result == 3

    def test_config_set_non_numeric_value(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("user.daily_goal_hours", "abc")
        assert result is False

    def test_config_set_non_numeric_threshold(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("thresholds.weakness_score", "abc")
        assert result is False

    def test_config_set_non_numeric_forget_days(self, temp_data_dir):
        store = ConfigStore(temp_data_dir)
        result = store.set_value("thresholds.forget_days", "abc")
        assert result is False

    def test_memory_store_empty_file(self, temp_data_dir):
        store = MemoryStore(temp_data_dir)
        records = store.get_all_records()
        assert records == []

    def test_memory_store_invalid_json(self, temp_data_dir):
        filepath = os.path.join(temp_data_dir, "memory.json")
        with open(filepath, "w") as f:
            f.write("invalid json")
        store = MemoryStore(temp_data_dir)
        records = store.get_all_records()
        assert records == []

    def test_config_store_invalid_json(self, temp_data_dir):
        filepath = os.path.join(temp_data_dir, "config.json")
        with open(filepath, "w") as f:
            f.write("invalid json")
        store = ConfigStore(temp_data_dir)
        config = store.load_config()
        assert config.user.name == "考生"


class TestAdditionalCases:
    def test_chapter_by_number(self):
        from commands.submit import prompt_chapter
        mock_config = MagicMock()
        mock_config.get_subject_chapters.return_value = ["线性表", "栈和队列", "树与二叉树"]
        
        with patch("builtins.input", side_effect=["2"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_chapter(mock_config, "数据结构")
            assert result == "栈和队列"

    def test_chapter_by_text(self):
        from commands.submit import prompt_chapter
        mock_config = MagicMock()
        mock_config.get_subject_chapters.return_value = ["线性表", "栈和队列"]
        
        with patch("builtins.input", side_effect=["自定义章节"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_chapter(mock_config, "数据结构")
            assert result == "自定义章节"

    def test_chapter_number_out_of_range(self):
        from commands.submit import prompt_chapter
        mock_config = MagicMock()
        mock_config.get_subject_chapters.return_value = ["线性表", "栈和队列"]
        
        with patch("builtins.input", side_effect=["5", "线性表"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_chapter(mock_config, "数据结构")
            assert result == "5"

    def test_duration_exactly_16(self):
        from commands.submit import prompt_duration
        with patch("builtins.input", side_effect=["16"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_duration()
            assert result == 16.0

    def test_duration_exactly_0(self):
        from commands.submit import prompt_duration
        with patch("builtins.input", side_effect=["0"]), \
             patch("sys.stdout", new_callable=StringIO):
            result = prompt_duration()
            assert result == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
