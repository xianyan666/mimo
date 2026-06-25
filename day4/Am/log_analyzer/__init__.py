"""log_analyzer — Apache 日志智能分析工具库。"""

from .log_parser import parse_log_file, parse_log_line
from .error_filter import enrich_errors, filter_errors
from .statistics import daily_error_count, error_code_stats, module_error_stats, category_stats
from .visualizer import plot_daily_error_trend, plot_error_code_pie, plot_module_error_bar
from .utils import safe_read_csv, parse_timestamp, ensure_dir, CHARTS_DIR

__all__ = [
    'parse_log_file', 'parse_log_line',
    'enrich_errors', 'filter_errors',
    'daily_error_count', 'error_code_stats', 'module_error_stats', 'category_stats',
    'plot_daily_error_trend', 'plot_error_code_pie', 'plot_module_error_bar',
    'safe_read_csv', 'parse_timestamp', 'ensure_dir',
]
