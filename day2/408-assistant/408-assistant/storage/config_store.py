import os

from models.config import Config, get_default_config
from storage.file_utils import safe_read_json, write_json


class ConfigStore:
    def __init__(self, data_dir: str = "data"):
        self.filepath = os.path.join(data_dir, "config.json")
        self._config = None

    def _load(self) -> dict:
        default_config = get_default_config()
        default = default_config.to_dict()
        return safe_read_json(self.filepath, default)

    def load_config(self) -> Config:
        if self._config is None:
            data = self._load()
            self._config = Config.from_dict(data)
        return self._config

    def save_config(self, config: Config) -> None:
        self._config = config
        write_json(self.filepath, config.to_dict())

    def set_value(self, key: str, value: str) -> bool:
        config = self.load_config()

        keys = key.split('.')
        if len(keys) == 2:
            section, field = keys
            if section == "user":
                if field == "name":
                    config.user.name = value
                elif field == "target_date":
                    config.user.target_date = value
                elif field == "daily_goal_hours":
                    try:
                        config.user.daily_goal_hours = float(value)
                    except ValueError:
                        return False
                else:
                    return False
            elif section == "thresholds":
                if field == "weakness_score":
                    try:
                        config.thresholds.weakness_score = float(value)
                    except ValueError:
                        return False
                elif field == "forget_days":
                    try:
                        config.thresholds.forget_days = int(value)
                    except ValueError:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False

        self.save_config(config)
        return True

    def get_subject_names(self) -> list[str]:
        config = self.load_config()
        return [s.name for s in config.subjects]

    def get_subject_chapters(self, subject_name: str) -> list[str]:
        config = self.load_config()
        for s in config.subjects:
            if s.name == subject_name:
                return s.chapters
        return []
