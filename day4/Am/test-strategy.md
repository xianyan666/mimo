# test-strategy.md — 测试策略文档

## 1. 总体测试策略

### 1.1 测试方法

| 方法 | 说明 | 适用范围 |
|------|------|----------|
| 手动验证 | 运行脚本 + 检查输出数据 | 主要方法，覆盖全部功能点 |
| 自动化思路 | 提供 pytest 测试用例设计思路 | 辅助，展示测试意识 |

### 1.2 测试层次

| 层次 | 说明 | 对应课程 |
|------|------|----------|
| 单元测试 | 单个函数的输入输出验证 | L1/L2/L3 |
| 集成测试 | 脚本端到端运行，检查中间文件 | L1→L2→L3 |
| 验收测试 | 交付物完整性检查 | 最终 |

### 1.3 验证工具

```bash
# 数据验证
python -c "import pandas as pd; df = pd.read_csv('xxx.csv'); print(len(df))"

# 脚本运行
python lesson1_日志探索与解析.py
python lesson2_异常识别与统计.py
python lesson3_可视化与报告.py

# 文件检查
ls -la charts/  # 检查图表文件
wc -l *.csv     # 检查 CSV 行数
```

---

## 2. Lesson 1 测试：日志解析与结构化输出

### 2.1 测试用例

| 编号 | 测试项 | 输入 | 预期输出 | 验证方法 | 结果 |
|------|--------|------|----------|----------|------|
| TC1.1 | CSV 行数 | Apache.log (56,482 行) | structured_logs.csv = 56,482 行 | `wc -l structured_logs.csv` → 56,483（含表头） | Pass |
| TC1.2 | CSV 列名 | — | timestamp, level, content | `head -1 structured_logs.csv` | Pass |
| TC1.3 | 标准行解析 | `[Thu Jun 09 06:07:04 2005] [notice] LDAP:...` | timestamp=Thu Jun 09 06:07:04 2005, level=notice | `python -c "import pandas as pd; print(pd.read_csv('structured_logs.csv').iloc[0])"` | Pass |
| TC1.4 | 异常行保留 | `script not found or unable to stat` | timestamp="", level=unknown, content=原始行 | `python -c "df=pd.read_csv('structured_logs.csv'); print(df[df['level']=='unknown'].iloc[0])"` | Pass |
| TC1.5 | unknown 行数 | — | 4,478 行 | `python -c "df=pd.read_csv('structured_logs.csv'); print(len(df[df['level']=='unknown']))"` → 4,478 | Pass |
| TC1.6 | 级别分布 | — | error:38,081 / notice:13,755 / warn:168 / unknown:4,478 | `python -c "df=pd.read_csv('structured_logs.csv'); print(df['level'].value_counts())"` | Pass |
| TC1.7 | timestamp 非空率 | 标准行 | 100%（标准行 timestamp 均非空） | `python -c "df=pd.read_csv('structured_logs.csv'); print(df[df['level']!='unknown']['timestamp'].notna().mean())"` → 1.0 | Pass |
| TC1.8 | 脚本无报错 | `python lesson1_日志探索与解析.py` | 正常输出统计结果 | 运行脚本，检查退出码 | Pass |

### 2.2 自动化测试思路（pytest）

```python
import pandas as pd
from log_parser import parse_log_line, parse_log_file

def test_parse_standard_line():
    r = parse_log_line('[Thu Jun 09 06:07:04 2005] [notice] test content')
    assert r['timestamp'] == 'Thu Jun 09 06:07:04 2005'
    assert r['level'] == 'notice'
    assert r['content'] == 'test content'

def test_parse_abnormal_line():
    r = parse_log_line('script not found or unable to stat')
    assert r['timestamp'] == ''
    assert r['level'] == 'unknown'
    assert r['content'] == 'script not found or unable to stat'

def test_parse_file_row_count():
    df = parse_log_file('Apache.log')
    assert len(df) == 56482

def test_parse_file_columns():
    df = parse_log_file('Apache.log')
    assert list(df.columns) == ['timestamp', 'level', 'content']

def test_unknown_count():
    df = parse_log_file('Apache.log')
    assert len(df[df['level'] == 'unknown']) == 4478
```

---

## 3. Lesson 2 测试：异常识别与统计分析

### 3.1 测试用例

| 编号 | 测试项 | 输入 | 预期输出 | 验证方法 | 结果 |
|------|--------|------|----------|----------|------|
| TC2.1 | error_logs.csv 行数 | structured_logs.csv | 38,081 行 | `wc -l error_logs.csv` → 38,082（含表头） | Pass |
| TC2.2 | error_logs.csv 列名 | — | timestamp, level, content, module, error_code, category | `head -1 error_logs.csv` | Pass |
| TC2.3 | module 分布 | — | 7 个模块：other/workerEnv/mod_jk/jk2_init/config/env/uriMap | `python -c "df=pd.read_csv('error_logs.csv'); print(df['module'].value_counts())"` | Pass |
| TC2.4 | workerEnv 优先级 | content 含 workerEnv | module=workerEnv（非 mod_jk） | `python -c "df=pd.read_csv('error_logs.csv'); print(df[df['module']=='workerEnv'].iloc[0]['content'][:60])"` | Pass |
| TC2.5 | error_code 种类 | — | 19 种 | `python -c "df=pd.read_csv('error_logs.csv'); print(df['error_code'].nunique())"` → 19 | Pass |
| TC2.6 | category 分布 | — | HTTP客户端请求错误:31,115 / 服务端模块错误:6,966 | `python -c "df=pd.read_csv('error_logs.csv'); print(df['category'].value_counts())"` | Pass |
| TC2.7 | error_code_stats.csv | — | 19 行，占比总和 ≈ 100% | `python -c "df=pd.read_csv('error_code_stats.csv'); print(len(df), df['percentage'].sum())"` → 19, 100.01% | Pass |
| TC2.8 | module_error_stats.csv | — | 7 行 | `wc -l module_error_stats.csv` → 8（含表头） | Pass |
| TC2.9 | error_code_reference.csv | — | 18 行，5 列 | `python -c "df=pd.read_csv('error_code_reference.csv'); print(len(df), list(df.columns))"` → 18, 5列 | Pass |
| TC2.10 | 筛选功能 | module=mod_jk | 返回 1,259 行 | `python -c "from error_filter import *; df=pd.read_csv('structured_logs.csv'); e=enrich_errors(df); print(len(filter_errors(e, module='mod_jk')))"` → 1259 | Pass |
| TC2.11 | 脚本无报错 | `python lesson2_异常识别与统计.py` | 正常输出统计结果 | 运行脚本，检查退出码 | Pass |

### 3.2 自动化测试思路（pytest）

```python
import pandas as pd
from error_filter import enrich_errors, filter_errors, extract_module, extract_error_code
from statistics import error_code_stats, module_error_stats

def test_enrich_errors_columns():
    df = pd.read_csv('structured_logs.csv')
    errors = enrich_errors(df)
    assert 'module' in errors.columns
    assert 'error_code' in errors.columns
    assert 'category' in errors.columns

def test_workerEnv_priority():
    assert extract_module('mod_jk child workerEnv in error state 6') == 'workerEnv'
    assert extract_module('mod_jk child init 1 -2') == 'mod_jk'

def test_filter_by_module():
    df = pd.read_csv('structured_logs.csv')
    errors = enrich_errors(df)
    result = filter_errors(errors, module='mod_jk')
    assert len(result) == 1259

def test_error_code_stats_sum():
    df = pd.read_csv('structured_logs.csv')
    errors = enrich_errors(df)
    stats = error_code_stats(errors)
    assert abs(stats['percentage'].sum() - 100) < 0.1
```

---

## 4. Lesson 3 测试：可视化与报告

### 4.1 测试用例

| 编号 | 测试项 | 输入 | 预期输出 | 验证方法 | 结果 |
|------|--------|------|----------|----------|------|
| TC3.1 | 趋势图生成 | daily_error_count() | charts/daily_error_trend.png 存在 | `ls -la charts/daily_error_trend.png` → 140.1K | Pass |
| TC3.2 | 饼图生成 | error_code_stats() | charts/error_code_pie.png 存在 | `ls -la charts/error_code_pie.png` → 88.7K | Pass |
| TC3.3 | 柱状图生成 | module_error_stats() | charts/module_error_bar.png 存在 | `ls -la charts/module_error_bar.png` → 45.3K | Pass |
| TC3.4 | 图表 DPI | — | 150 | `python -c "from PIL import Image; img=Image.open('charts/daily_error_trend.png'); print(img.info.get('dpi'))"` | Pass |
| TC3.5 | 包独立 import | `from log_analyzer import ...` | 无 ImportError | `python -c "from log_analyzer import parse_log_file"` | Pass |
| TC3.6 | 包模块完整性 | — | 7 个文件 | `ls log_analyzer/*.py` → 6 个 .py + README.md | Pass |
| TC3.7 | report 章节数 | — | 8 个顶级章节 | `python -c "...顶级章节计数..."` → 8 | Pass |
| TC3.8 | 脚本无报错 | `python lesson3_可视化与报告.py` | 正常输出统计结果 + 图表路径 | 运行脚本，检查退出码 | Pass |

### 4.2 自动化测试思路（pytest）

```python
import os
from log_analyzer import (
    plot_daily_error_trend, plot_error_code_pie, plot_module_error_bar,
    safe_read_csv, daily_error_count, error_code_stats, module_error_stats,
)

def test_daily_trend_chart_created():
    df = safe_read_csv('structured_logs.csv')
    errors = df[df['level'] == 'error'].copy()
    daily = daily_error_count(errors)
    path = plot_daily_error_trend(daily)
    assert os.path.exists(path)
    assert path.endswith('.png')

def test_pie_chart_created():
    df = safe_read_csv('structured_logs.csv')
    errors = df[df['level'] == 'error'].copy()
    codes = error_code_stats(errors)
    path = plot_error_code_pie(codes)
    assert os.path.exists(path)

def test_bar_chart_created():
    df = safe_read_csv('structured_logs.csv')
    errors = df[df['level'] == 'error'].copy()
    modules = module_error_stats(errors)
    path = plot_module_error_bar(modules)
    assert os.path.exists(path)

def test_report_sections():
    with open('analysis_report.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sections = [l for l in lines if l.startswith('## ') and not l.startswith('### ')]
    assert len(sections) == 8
```

---

## 5. 最终验收

### 5.1 交付物 Checklist

| 编号 | 交付物 | 状态 | 说明 |
|------|--------|------|------|
| D1 | `structured_logs.csv` | ✅ | 56,482 行，含 unknown 异常行 |
| D2 | `error_logs.csv` | ✅ | 38,081 行，含 module/error_code/category 特征列 |
| D3 | `error_code_stats.csv` | ✅ | 19 行，占比总和 ≈ 100% |
| D4 | `module_error_stats.csv` | ✅ | 7 行 |
| D5 | `error_code_reference.csv` | ✅ | 18 行，5 列 |
| D6 | `charts/daily_error_trend.png` | ✅ | 140.1K，12x6，dpi=150 |
| D7 | `charts/error_code_pie.png` | ✅ | 88.7K，8x8，dpi=150 |
| D8 | `charts/module_error_bar.png` | ✅ | 45.3K，10x6，dpi=150 |
| D9 | `analysis_report.md` | ✅ | 8 章节，含根因分析和优化建议 |
| D10 | `log_analyzer/` 包 | ✅ | 7 文件，可独立 import |
| D11 | `prd.md` | ✅ | 产品需求文档 |
| D12 | `design.md` | ✅ | 技术设计文档 |
| D13 | `dev.md` | ✅ | 开发文档 |
| D14 | `test-strategy.md` | ✅ | 测试策略文档（本文件） |
| D15 | `ai-log.md` | ✅ | AI 协作记录（3 条） |
| D16 | `lesson1_日志探索与解析.py` | ✅ | L1 演示脚本 |
| D17 | `lesson2_异常识别与统计.py` | ✅ | L2 演示脚本 |
| D18 | `lesson3_可视化与报告.py` | ✅ | L3 演示脚本 |
| D19 | `log_parser.py` | ✅ | 根目录日志解析模块 |
| D20 | `error_filter.py` | ✅ | 根目录异常筛选模块 |
| D21 | `statistics.py` | ✅ | 根目录统计分析模块 |

### 5.2 验收标准验证

| 编号 | 验收标准 | 验证方法 | 结果 |
|------|----------|----------|------|
| AC1 | 能成功读取日志文件 | `parse_log_file('Apache.log')` 返回 56,482 行 | Pass |
| AC2 | 能生成 structured_logs.csv | 文件存在，行数 56,482 | Pass |
| AC3 | CSV 包含标准行和异常行 | unknown 行数 4,478 | Pass |
| AC4 | 能统计总行数、各级别数量 | error:38,081 / notice:13,755 / warn:168 / unknown:4,478 | Pass |
| AC5 | 能生成 error_logs.csv | 文件存在，行数 38,081 | Pass |
| AC6 | 能生成 error_code_stats.csv | 文件存在，19 行 | Pass |
| AC7 | 能生成 module_error_stats.csv | 文件存在，7 行 | Pass |
| AC8 | 能生成 error_code_reference.csv | 文件存在，18 行 | Pass |
| AC9 | 能说明主要错误类型和模块 | 见 analysis_report.md 第 4/5 章 | Pass |
| AC10 | charts/ 下生成 3 张 PNG | 3 个文件均存在且大小合理 | Pass |
| AC11 | log_analyzer/ 包结构完整 | 7 文件，独立 import 成功 | Pass |
| AC12 | analysis_report.md 包含 8 章节 | 顶级章节计数 = 8 | Pass |
| AC13 | 根因分析基于实际统计数据 | 报告中引用具体数值 | Pass |

### 5.3 测试总结

- **总测试用例**：27 项（L1:8 + L2:11 + L3:8）
- **通过**：27 项
- **失败**：0 项
- **交付物**：21 项全部齐全
- **验收标准**：13 项全部通过
