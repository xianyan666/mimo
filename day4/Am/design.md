# design.md — 技术设计文档

## 1. 总体技术设计

### 1.1 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主语言 |
| pandas | 2.x | 数据处理与分析 |
| re | 内置 | 正则表达式解析 |
| matplotlib | 3.x | 可视化图表生成 |

### 1.2 总体数据流

```
Apache.tar.gz
    │
    ▼
[Lesson 1] log_parser.parse_log_file()
    │
    ├──▶ structured_logs.csv (56,482 行)
    │       列: timestamp, level, content
    │
    ▼
[Lesson 2] error_filter.enrich_errors() + filter_errors()
    │
    ├──▶ error_logs.csv (38,081 行)
    │       列: timestamp, level, content, module, error_code, category
    │
    ├──▶ error_code_stats.csv (19 行)
    │       列: error_code, count, percentage
    │
    ├──▶ module_error_stats.csv (7 行)
    │       列: module, error_count, total_count, error_rate
    │
    └──▶ error_code_reference.csv (18 行)
            列: error_code, error_type, error_category, meaning, suggestion
    │
    ▼
[Lesson 3] visualizer + analysis_report.md
    │
    ├──▶ charts/daily_error_trend.png (12x6, dpi=150)
    ├──▶ charts/error_code_pie.png (8x8, dpi=150)
    ├──▶ charts/module_error_bar.png (10x6, dpi=150)
    └──▶ analysis_report.md (8 章节)
```

### 1.3 总体模块划分

| 模块 | 文件 | 职责 |
|------|------|------|
| 日志解析 | `log_parser.py` | 正则提取 timestamp / level / content，异常行保留为 unknown |
| 异常筛选 | `error_filter.py` | 特征提取（module / error_code / category）+ 多维度筛选 |
| 统计分析 | `statistics.py` | 每日趋势、错误码分布、模块异常率、大类统计 |
| 可视化 | `visualizer.py` | 折线图、饼图、柱状图生成 |
| 工具函数 | `utils.py` | 路径常量、目录创建、时间解析、安全读取 CSV、中文字体检测 |

---

## 2. Lesson 1 设计：日志解析与结构化输出

### 2.1 正则表达式设计

```python
LOG_PATTERN = re.compile(r'^\[(?P<timestamp>.*?)\]\s+\[(?P<level>\w+)\]\s+(?P<content>.*)$')
```

**命名组说明：**

| 命名组 | 匹配规则 | 示例 |
|--------|----------|------|
| `(?P<timestamp>.*?)` | 非贪婪匹配 `[` 和 `]` 之间的任意字符 | `Thu Jun 09 06:07:04 2005` |
| `(?P<level>\w+)` | 匹配一个或多个字母数字 | `notice` / `error` / `warn` |
| `(?P<content>.*)` | 匹配剩余所有内容 | `LDAP: Built with OpenLDAP LDAP SDK` |

**异常行处理：** 无法匹配的日志行返回 `{"timestamp": "", "level": "unknown", "content": 原始行}`。

### 2.2 核心函数签名

```python
def parse_log_line(line: str) -> dict:
    """解析单行日志。
    返回: {"timestamp": str, "level": str, "content": str}
    标准行: level 为 notice/error/warn
    异常行: timestamp="", level="unknown", content=原始行
    """

def parse_log_file(path: str, chunk_size: int = 10000) -> pd.DataFrame:
    """读取日志文件，返回结构化 DataFrame。
    输入: 日志文件路径
    输出: DataFrame[timestamp, level, content]
    特性: 分块读取，适合大文件
    """
```

### 2.3 数据契约

**输入：** Apache.log（原始日志文件，每行格式为 `[timestamp] [level] content` 或非标准格式）

**输出：** `structured_logs.csv`

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | string | 日志时间，格式 `Thu Jun 09 06:07:04 2005`，异常行为 `""` |
| `level` | string | 日志级别：`notice` / `error` / `warn` / `unknown` |
| `content` | string | 日志内容 |

### 2.4 分块读取策略

```python
chunk_size = 10000  # 每次读取行数
buffer = []         # 行缓冲区
for line in f:
    buffer.append(line)
    if len(buffer) >= chunk_size:
        records.extend(_parse_chunk(buffer))
        buffer = []
```

适用于大规模日志文件，避免一次性加载全部内容到内存。

---

## 3. Lesson 2 设计：异常识别与统计分析

### 3.1 特征提取规则

#### 3.1.1 module 提取（优先级从高到低）

| 优先级 | 模块名 | 匹配规则 |
|--------|--------|----------|
| 1 | `workerEnv` | content 包含 `workerEnv` |
| 2 | `mod_jk` | content 以 `mod_jk` 开头 |
| 3 | `jk2_init` | content 以 `jk2_init` 开头 |
| 4 | `env` | content 以 `env.` 开头 |
| 5 | `config` | content 以 `config.` 开头 |
| 6 | `uriMap` | content 以 `uriMap` 开头 |
| 7 | `other` | 以上均不匹配 |

#### 3.1.2 error_code 映射规则

| 匹配条件 | error_code |
|----------|------------|
| content 包含 `error state (\d+)` | `mod_jk_state_{N}` (N=1~10) |
| content 包含 `mod_jk child init` | `mod_jk_child_init` |
| content 以 `jk2_init` 开头 | `jk2_init` |
| content 包含 `env.createBean2` | `env_createBean` |
| content 包含 `config.update` | `config_update` |
| content 以 `uriMap` 开头 | `uriMap` |
| content 包含 `Directory index forbidden` | `HTTP_403` |
| content 包含 `File does not exist` | `HTTP_404` |
| content 包含 `script not found or unable to stat` | `HTTP_500` |
| 以上均不匹配 | `unknown` |

#### 3.1.3 category 映射规则

| 匹配条件 | category |
|----------|----------|
| content 包含 `[client` 或 匹配 HTTP 错误关键词 | `HTTP客户端请求错误` |
| 其他 | `服务端模块错误` |

### 3.2 核心函数签名

```python
# ── error_filter.py ──

def extract_module(content: str) -> str:
    """从 content 提取模块名。workerEnv 优先级高于 mod_jk。"""

def extract_error_code(content: str) -> str:
    """从 content 提取错误码标识。"""

def extract_category(content: str) -> str:
    """将错误归入大类。"""

def enrich_errors(df: pd.DataFrame) -> pd.DataFrame:
    """为 error 行添加特征列。
    输入: DataFrame[timestamp, level, content]
    输出: DataFrame[timestamp, level, content, module, error_code, category]
    筛选: 仅处理 level='error' 的行
    """

def filter_errors(
    df: pd.DataFrame,
    level: str | None = None,
    keyword: str | None = None,
    module: str | None = None,
    error_code: str | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """多维度筛选异常日志。参数均为可选，None 表示不限制。"""

# ── statistics.py ──

def daily_error_count(errors: pd.DataFrame) -> pd.DataFrame:
    """统计每日 Error 数量。
    输出: DataFrame[date, error_count]
    """

def error_code_stats(errors: pd.DataFrame) -> pd.DataFrame:
    """统计各错误码次数与占比。
    输出: DataFrame[error_code, count, percentage]
    """

def module_error_stats(errors: pd.DataFrame) -> pd.DataFrame:
    """统计各模块异常数量与异常率。
    输出: DataFrame[module, error_count, total_count, error_rate]
    """

def category_stats(errors: pd.DataFrame) -> pd.DataFrame:
    """按大类统计数量与占比。
    输出: DataFrame[category, count, percentage]
    """
```

### 3.3 数据契约

**输入：** `structured_logs.csv`（Lesson 1 输出）

**输出：**

| 文件 | 行数 | 列 |
|------|------|----|
| `error_logs.csv` | 38,081 | timestamp, level, content, module, error_code, category |
| `error_code_stats.csv` | 19 | error_code, count, percentage |
| `module_error_stats.csv` | 7 | module, error_count, total_count, error_rate |
| `error_code_reference.csv` | 18 | error_code, error_type, error_category, meaning, suggestion |

---

## 4. Lesson 3 设计：可视化与包封装

### 4.1 图表规格

#### 4.1.1 每日 Error 趋势折线图

| 属性 | 值 |
|------|-----|
| 文件名 | `charts/daily_error_trend.png` |
| 图表类型 | 折线图 + 填充区域 |
| 输入数据 | `daily_error_count()` → DataFrame[date, error_count] |
| 尺寸 | 12 x 6 英寸 |
| dpi | 150 |
| 线条颜色 | `#2196F3` |
| 填充透明度 | alpha=0.15 |
| 标题 | `Apache 每日 Error 数量趋势` |
| 中文字体 | SimHei / Microsoft YaHei（自动检测） |
| x 轴 | 日期，旋转 45° |
| y 轴 | Error 数量 |
| 网格 | y 轴方向，alpha=0.3 |

#### 4.1.2 错误码占比饼图

| 属性 | 值 |
|------|-----|
| 文件名 | `charts/error_code_pie.png` |
| 图表类型 | 饼图 |
| 输入数据 | `error_code_stats()` → DataFrame[error_code, count, percentage] |
| 尺寸 | 8 x 8 英寸 |
| dpi | 150 |
| Top N | 8（其余合并为"其他"） |
| 起始角度 | 140° |
| 标签字号 | 9pt |
| 百分比字号 | 8pt |
| 配色 | 9 色预设：`#E53935, #1E88E5, #43A047, #FB8C00, #8E24AA, #00ACC1, #F4511E, #6D4C41, #757575` |
| 标题 | `Error 错误码占比分布` |

#### 4.1.3 模块 Error 柱状图

| 属性 | 值 |
|------|-----|
| 文件名 | `charts/module_error_bar.png` |
| 图表类型 | 柱状图 |
| 输入数据 | `module_error_stats()` → DataFrame[module, error_count] |
| 尺寸 | 10 x 6 英寸 |
| dpi | 150 |
| 柱体颜色 | 6 色预设 |
| 数值标签 | 柱顶居中显示，字号 9pt |
| 标题 | `各模块 Error 数量对比` |
| 网格 | y 轴方向，alpha=0.3 |

### 4.2 log_analyzer/ 包结构

```
log_analyzer/
├── __init__.py        # 统一导出公共 API
├── log_parser.py      # 日志解析（自含，不依赖根目录）
├── error_filter.py    # 异常筛选与特征提取（自含）
├── statistics.py      # 统计分析（自含）
├── visualizer.py      # 可视化（自含）
├── utils.py           # 通用工具
└── README.md          # 模块说明与使用示例
```

**设计原则：**
- 包内模块自含完整代码，不 import 根目录模块
- 可独立分发使用（复制 `log_analyzer/` 目录即可）
- `__init__.py` 统一导出所有公共 API

### 4.3 utils.py 工具函数

```python
# ── 路径常量 ──
BASE_DIR: str       # 项目根目录
DATA_DIR: str       # 数据文件目录
CHARTS_DIR: str     # 图表输出目录
STRUCTURED_CSV: str # structured_logs.csv 路径
ERROR_CSV: str      # error_logs.csv 路径
REFERENCE_CSV: str  # error_code_reference.csv 路径
APACHE_LOG: str     # Apache.log 路径

def ensure_dir(path: str) -> None:
    """确保目录存在，不存在则创建。"""

def parse_timestamp(ts: str) -> datetime | None:
    """解析 Apache 日志时间戳。格式: 'Thu Jun 09 06:07:04 2005'"""

def safe_read_csv(path: str) -> pd.DataFrame:
    """安全读取 CSV，自动尝试 utf-8-sig / utf-8 / gbk / latin-1 编码。"""

def get_chinese_font() -> str:
    """返回系统可用的中文字体名称。优先: SimHei > Microsoft YaHei > STHeiti > ..."""
```

### 4.4 核心函数签名

```python
# ── visualizer.py ──

def plot_daily_error_trend(daily: pd.DataFrame, save_dir: str | None = None) -> str:
    """每日 Error 趋势折线图。
    输入: DataFrame[date, error_count]
    输出: PNG 文件路径
    """

def plot_error_code_pie(code_stats: pd.DataFrame, top_n: int = 8, save_dir: str | None = None) -> str:
    """错误码占比饼图（Top N，其余合并为"其他"）。
    输入: DataFrame[error_code, count, percentage]
    输出: PNG 文件路径
    """

def plot_module_error_bar(module_stats: pd.DataFrame, save_dir: str | None = None) -> str:
    """各模块 Error 数量柱状图（带数值标签）。
    输入: DataFrame[module, error_count]
    输出: PNG 文件路径
    """
```

### 4.5 数据契约

**输入：** `structured_logs.csv` + `error_logs.csv`（Lesson 1/2 输出）

**输出：**

| 文件 | 说明 |
|------|------|
| `charts/daily_error_trend.png` | 每日 Error 趋势折线图 |
| `charts/error_code_pie.png` | Top 8 错误码占比饼图 |
| `charts/module_error_bar.png` | 各模块 Error 数量柱状图 |
| `analysis_report.md` | 8 章节分析报告 |

---

## 5. 模块依赖关系

```
log_parser.py  ←──  error_filter.py  ←──  statistics.py
      │                   │                    │
      │                   │                    │
      └───────────────────┴────────────────────┘
                          │
                    visualizer.py
                          │
                       utils.py
```

- `error_filter` 依赖 `log_parser` 的输出 DataFrame 结构
- `statistics` 依赖 `error_filter` 的输出 DataFrame 结构（含 module / error_code / category 列）
- `visualizer` 依赖 `statistics` 的输出 DataFrame
- `utils` 被所有模块引用（路径常量、工具函数）
- 各模块通过 DataFrame 列名约定解耦，不直接 import 其他业务模块
