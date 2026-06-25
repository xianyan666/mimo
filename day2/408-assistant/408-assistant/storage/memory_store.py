import os
from datetime import date, datetime
from typing import Optional

from models.record import Record, generate_id
from storage.file_utils import safe_read_json, write_json, backup_file


class MemoryStore:
    def __init__(self, data_dir: str = "data"):
        self.filepath = os.path.join(data_dir, "memory.json")
        self._data = None

    def _load(self) -> dict:
        if self._data is None:
            default = {"records": [], "metadata": {"created_at": datetime.now().isoformat(), "last_updated": datetime.now().isoformat()}}
            self._data = safe_read_json(self.filepath, default)
        return self._data

    def _save(self) -> None:
        if self._data:
            self._data["metadata"]["last_updated"] = datetime.now().isoformat()
            write_json(self.filepath, self._data)

    def save_record(self, record: Record) -> None:
        data = self._load()
        data["records"].append(record.to_dict())
        self._save()

    def get_all_records(self) -> list[Record]:
        data = self._load()
        return [Record.from_dict(r) for r in data.get("records", [])]

    def get_records_by_date(self, target_date: str) -> list[Record]:
        all_records = self.get_all_records()
        return [r for r in all_records if r.date == target_date]

    def get_records_by_subject(self, subject: str) -> list[Record]:
        all_records = self.get_all_records()
        return [r for r in all_records if r.subject == subject]

    def get_records_by_date_range(self, start_date: str, end_date: str) -> list[Record]:
        all_records = self.get_all_records()
        return [r for r in all_records if start_date <= r.date <= end_date]

    def get_today_records(self) -> list[Record]:
        today = date.today().isoformat()
        return self.get_records_by_date(today)

    def has_records(self) -> bool:
        return len(self.get_all_records()) > 0

    def get_unique_dates(self) -> list[str]:
        all_records = self.get_all_records()
        return sorted(set(r.date for r in all_records), reverse=True)

    def get_unique_subjects(self) -> list[str]:
        all_records = self.get_all_records()
        return sorted(set(r.subject for r in all_records))
