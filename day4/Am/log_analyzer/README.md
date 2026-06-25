# log_analyzer — Apache 日志智能分析工具库

## 模块组成

| 模块 | 功能 |
|------|------|
| `log_parser.py` | 日志解析：正则提取 timestamp / level / content |
| `error_filter.py` | 异常筛选与特征提取：module / error_code / category |
| `statistics.py` | 统计分析：每日趋势、错误码分布、模块异常率 |
| `visualizer.py` | 可视化：折线图、饼图、柱状图 |
| `utils.py` | 通用工具：路径常量、时间解析、安全读取 CSV |

## 安装

本包为纯 Python 模块，无需安装。将 `log_analyzer/` 目录复制到项目中即可使用。

依赖：`pandas`、`matplotlib`

## 使用示例

```python
from log_analyzer import (
    parse_log_file, safe_read_csv, enrich_errors, filter_errors,
    daily_error_count, error_code_stats, module_error_stats,
    plot_daily_error_trend, plot_error_code_pie, plot_module_error_bar,
)

# 从 CSV 读取已解析的日志
df = safe_read_csv('structured_logs.csv')

# 特征提取
errors = enrich_errors(df)

# 多维度筛选
mod_jk_errors = filter_errors(errors, module='mod_jk')

# 统计
daily = daily_error_count(errors)
codes = error_code_stats(errors)
modules = module_error_stats(errors)

# 可视化
plot_daily_error_trend(daily)
plot_error_code_pie(codes)
plot_module_error_bar(modules)
```
