import json
import os
import shutil
from pathlib import Path


def ensure_dir(dir_path: str) -> None:
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def safe_read_json(filepath: str, default: dict = None) -> dict:
    if default is None:
        default = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        write_json(filepath, default)
        return default
    except json.JSONDecodeError:
        backup_file(filepath)
        write_json(filepath, default)
        return default


def write_json(filepath: str, data: dict) -> None:
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def backup_file(filepath: str) -> None:
    if os.path.exists(filepath):
        backup_path = filepath.replace('.json', '_backup.json')
        shutil.copy2(filepath, backup_path)


def file_exists(filepath: str) -> bool:
    return os.path.exists(filepath)
