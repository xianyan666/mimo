"""日志解析模块。"""

import re
import pandas as pd

LOG_PATTERN = re.compile(r'^\[(?P<timestamp>.*?)\]\s+\[(?P<level>\w+)\]\s+(?P<content>.*)$')


def parse_log_line(line: str) -> dict:
    """解析单行日志。标准格式返回 {timestamp, level, content}；异常行返回 {timestamp="", level="unknown", content=原始行}。"""
    m = LOG_PATTERN.match(line.strip())
    if m:
        return m.groupdict()
    return {
        'timestamp': '',
        'level': 'unknown',
        'content': line.strip(),
    }


def parse_log_file(path: str, chunk_size: int = 10000) -> pd.DataFrame:
    """读取日志文件，返回结构化 DataFrame。异常行保留为 level="unknown"。"""
    records = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        buffer = []
        for line in f:
            buffer.append(line)
            if len(buffer) >= chunk_size:
                records.extend(_parse_chunk(buffer))
                buffer = []
        if buffer:
            records.extend(_parse_chunk(buffer))
    return pd.DataFrame(records, columns=['timestamp', 'level', 'content'])


def _parse_chunk(lines: list[str]) -> list[dict]:
    return [parse_log_line(line) for line in lines if line.strip()]
