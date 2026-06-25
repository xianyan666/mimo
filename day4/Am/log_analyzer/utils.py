"""通用工具函数：路径常量、目录创建、时间解析、安全读取。"""

import os
from datetime import datetime

import pandas as pd

# ── 路径常量 ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
STRUCTURED_CSV = os.path.join(DATA_DIR, 'structured_logs.csv')
ERROR_CSV = os.path.join(DATA_DIR, 'error_logs.csv')
REFERENCE_CSV = os.path.join(DATA_DIR, 'error_code_reference.csv')
APACHE_LOG = os.path.join(DATA_DIR, 'Apache.log')


def ensure_dir(path: str) -> None:
    """确保目录存在，不存在则创建。"""
    os.makedirs(path, exist_ok=True)


def parse_timestamp(ts: str) -> datetime | None:
    """解析 Apache 日志时间戳，返回 datetime 或 None。

    格式: 'Thu Jun 09 06:07:04 2005'
    """
    try:
        return datetime.strptime(ts, '%a %b %d %H:%M:%S %Y')
    except (ValueError, TypeError):
        return None


def safe_read_csv(path: str) -> pd.DataFrame:
    """安全读取 CSV 文件，自动尝试常见编码。"""
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'latin-1'):
        try:
            return pd.read_csv(path, encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f'无法读取文件: {path}')


def get_chinese_font() -> str:
    """返回系统中可用的中文字体名称。"""
    import matplotlib.font_manager as fm
    candidates = ['SimHei', 'Microsoft YaHei', 'STHeiti', 'WenQuanYi Micro Hei', 'Arial Unicode MS']
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return 'DejaVu Sans'
