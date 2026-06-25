# dev.md — 开发文档

## 1. 环境搭建

### 1.1 基础环境

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 本机 3.13.5 |
| pandas | 2.x | 数据处理 |
| matplotlib | 3.x | 可视化 |
| re | 内置 | 正则表达式 |

### 1.2 安装步骤

```bash
# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install pandas matplotlib
```

无需额外配置，pandas 和 matplotlib 为唯二外部依赖。

---

## 2. 代码结构

### 2.1 完整目录树

```
day4/Am/
├── Apache.log                    # 原始日志文件（56,482 行）
├── Apache.tar.gz                 # 压缩包
├── 作业要求.md                    # 课程作业要求
│
├── log_parser.py                 # [L1] 可复用日志解析模块
├── lesson1_日志探索与解析.py       # [L1] 数据探索 + 解析脚本
├── structured_logs.csv           # [L1] 结构化日志（56,482 行）
│
├── error_filter.py               # [L2] 异常筛选与特征提取模块
├── statistics.py                 # [L2] 统计分析模块
├── lesson2_异常识别与统计.py       # [L2] 异常识别 + 统计脚本
├── error_logs.csv                # [L2] 异常日志子集（38,081 行）
├── error_code_stats.csv          # [L2] 错误码统计
├── module_error_stats.csv        # [L2] 模块异常统计
├── error_code_reference.csv      # [L2] 错误类型含义对照表
│
├── lesson3_可视化与报告.py         # [L3] 可视化 + 演示脚本
├── analysis_report.md            # [L3] 分析报告（8 章节）
│
├── prd.md                        # 产品需求文档
├── design.md                     # 技术设计文档
├── dev.md                        # 开发文档（本文件）
├── test-strategy.md              # 测试策略文档
├── ai-log.md                     # AI 协作记录
│
├── charts/                       # 可视化图表
│   ├── daily_error_trend.png     #   每日 Error 趋势折线图
│   ├── error_code_pie.png        #   错误码占比饼图
│   └── module_error_bar.png      #   模块 Error 柱状图
│
└── log_analyzer/                 # 工具库包（自含，可独立分发）
    ├── __init__.py               #   统一导出公共 API
    ├── log_parser.py             #   日志解析模块
    ├── error_filter.py           #   异常筛选与特征提取
    ├── statistics.py             #   统计分析
    ├── visualizer.py             #   可视化
    ├── utils.py                  #   通用工具函数
    └── README.md                 #   包说明文档
```

### 2.2 关键文件说明

| 文件 | 作用 | 核心导出 |
|------|------|----------|
| `log_parser.py` | 日志解析 | `parse_log_file()`, `parse_log_line()` |
| `error_filter.py` | 异常筛选与特征提取 | `enrich_errors()`, `filter_errors()` |
| `statistics.py` | 统计分析 | `daily_error_count()`, `error_code_stats()`, `module_error_stats()` |
| `log_analyzer/` | 工具库包 | 以上所有 + `visualizer`, `utils` |
| `lesson1/2/3_*.py` | 各课时演示脚本 | — |

---

## 3. Lesson 1 开发记录

### 3.1 功能点：日志解析模块

**目标：** 将原始 Apache.log 解析为结构化 DataFrame。

**实现：**
- 正则表达式采用命名组 `(?P<timestamp>.*?)` / `(?P<level>\w+)` / `(?P<content>.*)`
- 解析函数使用 `m.groupdict()` 直接返回 dict，代码更简洁
- 分块读取（chunk_size=10,000）避免大文件内存问题

**关键调整：**
- 初版异常行直接跳过（返回 None），后根据作业要求改为保留为 `level="unknown"`
- `_parse_chunk()` 从"过滤 None"改为"直接返回所有行"

### 3.2 功能点：数据探索

**目标：** 统计总行数、各级别数量、时间范围、异常行数。

**实现：**
- `explore_raw_logs()` 独立于 `parse_log_file()`，手动逐行正则匹配
- 异常行（不匹配标准格式）单独计数，同时计入 `unknown` 级别

**实际数据：**

| 指标 | 值 |
|------|-----|
| 总行数 | 56,482 |
| 标准格式 | 52,004 |
| 异常行 | 4,478 |
| error | 38,081 |
| notice | 13,755 |
| warn | 168 |
| 时间范围 | 2005-06-09 ~ 2006-02-28 |

### 3.3 遇到的问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 中文输出乱码 | Windows 终端编码非 UTF-8 | 数据正确，仅显示问题，不影响 CSV 输出 |
| `rtk python3` 报错 | rtk 找不到 python3 路径 | 改用 `python` 直接调用 |
| `rtk grep` 失败 | 系统无 ripgrep | 改用 Python 脚本做统计 |

---

## 4. Lesson 2 开发记录

### 4.1 功能点：特征提取

**目标：** 从 error 消息中提取 module、error_code、category 三个特征列。

**实现：**
- `extract_module()`：优先级链——workerEnv > mod_jk > jk2_init > env > config > uriMap > other
- `extract_error_code()`：正则匹配 + 关键词映射，共 19 种错误码
- `extract_category()`：基于 `[client` 关键词和 HTTP 错误关键词判断大类

**关键调整：**
- 初版 module 只有 mod_jk，后根据作业要求添加 workerEnv（优先级高于 mod_jk）
- 添加后 workerEnv 独占 4,349 条（11.42%），mod_jk 降至 1,259 条（3.31%）

### 4.2 功能点：多维度筛选

**目标：** 支持按 level、keyword、module、error_code、category 任意组合筛选。

**实现：**
- `filter_errors()` 采用链式过滤，每个参数为 None 时跳过该维度
- 输入 DataFrame 需先经过 `enrich_errors()` 处理（含特征列）

### 4.3 功能点：统计分析

**目标：** 每日趋势、错误码分布、模块异常率、大类统计。

**实现：**
- `daily_error_count()`：将 timestamp 字符串转为 date，按日分组计数
- `error_code_stats()` / `module_error_stats()` / `category_stats()`：value_counts + 占比计算

**关键调整：**
- 初版 lesson2 只打印统计结果，后根据作业要求补生成 `error_code_stats.csv` 和 `module_error_stats.csv`

### 4.4 遇到的问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `unknown` 错误码 208 条 | HTTP 攻击尝试（目录遍历 cmd.exe） | 保留为 unknown，不强行归类 |
| 模块统计 other 占比过高 | HTTP 客户端请求类错误首词不统一 | 符合预期，other 即"非服务端模块" |

---

## 5. Lesson 3 开发记录

### 5.1 功能点：可视化模块

**目标：** 生成三张图表（折线图、饼图、柱状图）。

**实现：**
- 使用 `matplotlib.use('Agg')` 避免 GUI 依赖
- 中文字体自动检测：SimHei > Microsoft YaHei > STHeiti > ...
- 饼图 Top N 合并：取前 8 个错误码，剩余合并为"其他"

**关键调整：**
- 初版 `__init__.py` 未导出 `CHARTS_DIR`，导致 lesson3 import 失败，补加导出

### 5.2 功能点：log_analyzer 包封装

**目标：** 将根目录模块整合为自含的 Python 包。

**实现：**
- 包内模块完整复制，不 import 根目录模块
- `__init__.py` 统一导出所有公共 API
- `utils.py` 提供路径常量、时间解析、安全读取、字体检测

**设计决策：**
- 根目录模块供 Lesson 1/2 独立使用
- log_analyzer 包供 Lesson 3 集成使用
- 两套代码保持同步，修改时需同时更新

### 5.3 功能点：分析报告

**目标：** 8 章节完整报告，基于实际统计数据。

**实现：**
- 直接使用 Lesson 1/2 的统计结果填充数据
- 故障根因分析基于错误模式推断（mod_jk 连接不稳定、404 死链接、配置缺失）
- 优化建议分 5 个优先级层次

### 5.4 遇到的问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ImportError: cannot import name 'CHARTS_DIR'` | `__init__.py` 未导出该常量 | 补加 `from .utils import CHARTS_DIR` |
| 图表中文显示方框 | matplotlib 未找到中文字体 | `get_chinese_font()` 自动检测可用字体 |

---

## 6. AI 协作说明

本项目在以下环节使用了 AI 辅助：

| 环节 | AI 辅助内容 | 人工判断 |
|------|------------|----------|
| 正则表达式 | AI 生成初稿 `^\[(?P<timestamp>.*?)\]...` | 采纳，命名组可读性更好 |
| 模块划分 | AI 提出 5 个决策点（异常行处理、模块定义等） | 全部采纳并确认 |
| 特征提取 | AI 设计 module 优先级链和 error_code 映射规则 | 采纳，补充 workerEnv 优先级 |
| 可视化 | AI 设计图表规格（尺寸、配色、字体） | 采纳 |
| 报告框架 | AI 生成 8 章节框架和根因分析初稿 | 人工校验数据准确性后采纳 |

详细 AI 协作记录见 `ai-log.md`（3 条记录，每课时 1 条）。
