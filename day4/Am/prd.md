# prd.md — 产品需求文档

## 1. 项目总体需求

### 1.1 项目背景

Apache HTTP Server 运行过程中产生大量错误日志，涵盖 HTTP 客户端请求错误（403/404/500）和服务端模块错误（mod_jk/jk2_init 等）。需要通过日志解析、异常识别、统计分析和可视化，辅助运维工程师定位故障根因并给出优化建议。

### 1.2 项目目标

完成以下全流程：

```
日志解析 → 异常识别 → 统计分析 → 可视化 → 报告输出
```

核心能力：正则表达式、数据解析、故障根因分析。

### 1.3 总体交付物

| 交付物 | 说明 |
|--------|------|
| `structured_logs.csv` | 结构化日志数据（含异常行） |
| `error_logs.csv` | 异常日志子集（含特征列） |
| `error_code_stats.csv` | 错误码统计表 |
| `module_error_stats.csv` | 模块异常统计表 |
| `error_code_reference.csv` | 错误类型含义对照表 |
| `charts/` | 可视化图表（3 张 PNG） |
| `analysis_report.md` | 分析报告（8 章节） |
| `log_analyzer/` | 工具库包 |
| `prd.md` | 产品需求文档 |
| `design.md` | 技术设计文档 |
| `dev.md` | 开发文档 |
| `test-strategy.md` | 测试策略文档 |
| `ai-log.md` | AI 协作记录 |

### 1.4 技术栈

- Python 3.10+
- pandas
- re（正则表达式）
- matplotlib

### 1.5 数据来源

- GitHub [logpai/loghub](https://github.com/logpai/loghub/tree/master/Apache)
- 数据文件：`Apache.tar.gz`，解压后约 56,000+ 条日志
- 日志格式：`[时间戳] [日志级别] 日志内容`

---

## 2. Lesson 1：日志探索与解析清洗需求

### 2.1 功能需求

| 编号 | 功能 | 说明 |
|------|------|------|
| F1.1 | 解压数据 | 解压 `Apache.tar.gz`，读取日志文件 |
| F1.2 | 数据探索 | 统计总行数、各级别日志数量、时间范围、检查异常行 |
| F1.3 | 正则解析 | 使用正则表达式提取 `timestamp`、`level`、`content` 三个字段 |
| F1.4 | 异常行保留 | 无法匹配标准格式的日志行保留为 `timestamp="" / level="unknown" / content=原始行` |
| F1.5 | 结构化输出 | 将解析结果保存为 `structured_logs.csv` |
| F1.6 | 大文件处理 | 了解分块读取思路，代码支持 chunk_size 参数 |

### 2.2 字段要求

`structured_logs.csv` 包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | string | 日志时间，格式如 `Thu Jun 09 06:07:04 2005`，异常行为空字符串 |
| `level` | string | 日志级别：`notice` / `error` / `warn` / `unknown` |
| `content` | string | 日志内容 |

### 2.3 异常行处理需求

无法匹配标准格式 `[timestamp] [level] content` 的日志行**不得丢弃**，保留为：

| 字段 | 值 |
|------|-----|
| `timestamp` | 空字符串 `""` |
| `level` | `"unknown"` |
| `content` | 原始整行内容 |

### 2.4 Lesson 1 验收标准

- [x] 能成功读取日志文件
- [x] 能生成 `structured_logs.csv`
- [x] CSV 中包含标准格式行和异常行（level="unknown"）
- [x] 能统计总行数、各级别日志数量（含 unknown）、异常行数量
- [x] 能输出时间范围

### 2.5 提交文件

| 文件 | 说明 |
|------|------|
| `lesson1_日志探索与解析.py` | 数据探索 + 解析流程脚本 |
| `log_parser.py` | 可复用的日志解析模块 |
| `structured_logs.csv` | 解析后的结构化数据 |

---

## 3. Lesson 2：异常识别与统计分析需求

### 3.1 功能需求

| 编号 | 功能 | 说明 |
|------|------|------|
| F2.1 | 按级别筛选 | 筛选 `level=error` 的日志 |
| F2.2 | 按关键词筛选 | 按 content 中的关键词筛选异常 |
| F2.3 | 按模块筛选 | 按模块名筛选异常 |
| F2.4 | 按错误码筛选 | 按 error_code 筛选异常 |
| F2.5 | 按大类筛选 | 按 category（HTTP客户端请求错误/服务端模块错误）筛选 |
| F2.6 | 提取错误码 | 从 content 中提取 error_code 字段 |
| F2.7 | 提取模块 | 从 content 中提取 module 字段 |
| F2.8 | 提取大类 | 从 content 中提取 category 字段 |
| F2.9 | 每日统计 | 统计每日 Error 数量趋势 |
| F2.10 | 错误码统计 | 统计各错误码出现次数与占比 |
| F2.11 | 模块统计 | 统计各模块异常数量与异常率 |
| F2.12 | 导出异常子集 | 将筛选出的异常日志保存为 `error_logs.csv` |
| F2.13 | 导出错误码统计 | 保存为 `error_code_stats.csv` |
| F2.14 | 导出模块统计 | 保存为 `module_error_stats.csv` |
| F2.15 | 导出错误码参考 | 保存为 `error_code_reference.csv` |

### 3.2 模块定义

按 Apache 日志内容中的组件或关键词识别模块，优先级从高到低：

| 优先级 | 模块 | 匹配规则 |
|--------|------|----------|
| 1 | `workerEnv` | content 包含 `workerEnv` |
| 2 | `mod_jk` | content 以 `mod_jk` 开头 |
| 3 | `jk2_init` | content 以 `jk2_init` 开头 |
| 4 | `env` | content 以 `env.` 开头 |
| 5 | `config` | content 以 `config.` 开头 |
| 6 | `uriMap` | content 以 `uriMap` 开头 |
| 7 | `other` | 以上均不匹配（主要为 HTTP 客户端请求错误） |

### 3.3 错误码定义

错误码同时包含以下类型：

**mod_jk 系列：**

| 错误码 | 含义 |
|--------|------|
| `mod_jk_state_1` ~ `mod_jk_state_10` | mod_jk worker 处于不同异常状态 |
| `mod_jk_child_init` | mod_jk 子进程初始化失败 |

**HTTP 系列：**

| 错误码 | 含义 |
|--------|------|
| `HTTP_403` | 目录索引被禁止（Directory index forbidden） |
| `HTTP_404` | 请求文件不存在（File does not exist） |
| `HTTP_500` | CGI 脚本未找到（script not found） |

**其他：**

| 错误码 | 含义 |
|--------|------|
| `jk2_init` | jk2 子进程注册信息 |
| `env_createBean` | JNI 通道创建失败 |
| `config_update` | 配置更新失败 |
| `uriMap` | URI 映射找不到主机 |
| `unknown` | 无法归类的错误 |

### 3.4 error_code_reference.csv 格式

| 字段 | 说明 |
|------|------|
| `error_code` | 错误码标识 |
| `error_type` | 错误类型描述 |
| `error_category` | 大类（HTTP客户端请求错误 / 服务端模块错误） |
| `meaning` | 错误含义说明 |
| `suggestion` | 处理建议 |

### 3.5 Lesson 2 验收标准

- [x] 能生成 `error_logs.csv`（含 module、error_code、category 特征列）
- [x] 能生成 `error_code_stats.csv`
- [x] 能生成 `module_error_stats.csv`
- [x] 能生成 `error_code_reference.csv`
- [x] 能说明主要错误类型和模块
- [x] 支持多维度组合筛选

### 3.6 提交文件

| 文件 | 说明 |
|------|------|
| `lesson2_异常识别与统计.py` | 异常识别 + 统计脚本 |
| `error_filter.py` | 异常筛选模块 |
| `statistics.py` | 统计分析模块 |
| `error_code_reference.csv` | 错误类型含义对照表 |

---

## 4. Lesson 3：可视化展示与报告总结需求

### 4.1 功能需求

| 编号 | 功能 | 说明 |
|------|------|------|
| F3.1 | 趋势图 | 生成每日 Error 数量变化趋势折线图 |
| F3.2 | 饼图 | 生成 Top N 错误码占比分布饼图 |
| F3.3 | 柱状图 | 生成各模块 Error 数量对比柱状图 |
| F3.4 | 工具库封装 | 将前三课模块整合为 `log_analyzer/` 包 |
| F3.5 | 报告撰写 | 生成 `analysis_report.md`（8 章节） |

### 4.2 图表需求

| 图表 | 文件名 | 尺寸 | 说明 |
|------|--------|------|------|
| 折线图 | `daily_error_trend.png` | 12x6 | 每日 Error 数量变化趋势，带填充区域 |
| 饼图 | `error_code_pie.png` | 8x8 | Top N 错误码占比，其余合并为"其他" |
| 柱状图 | `module_error_bar.png` | 10x6 | 各模块 Error 数量，带数值标签 |

**通用规格：**
- dpi = 150
- 中文字体：优先 SimHei / Microsoft YaHei
- 保存到 `charts/` 目录

### 4.3 log_analyzer/ 包结构

```
log_analyzer/
├── __init__.py        # 统一导出公共 API
├── log_parser.py      # 日志解析模块
├── error_filter.py    # 异常筛选与特征提取模块
├── statistics.py      # 统计分析模块
├── visualizer.py      # 可视化模块
├── utils.py           # 通用工具（路径常量、时间解析、安全读取）
└── README.md          # 模块说明与使用示例
```

**要求：** 包内模块自含完整代码，不依赖根目录模块，可独立分发使用。

### 4.4 analysis_report.md 章节

| 章节 | 内容 |
|------|------|
| 1. 项目概述 | 项目背景、目标、技术栈、数据来源 |
| 2. 数据探索 | 总行数、各级别数量、时间范围、异常行统计 |
| 3. 日志解析方法 | 正则表达式设计、字段提取逻辑、分块读取策略 |
| 4. 异常识别结果 | 三维度筛选结果、错误码分布、模块分布 |
| 5. 统计分析结果 | 大类分布、每日趋势、模块异常率 |
| 6. 可视化分析 | 三张图表的描述与解读 |
| 7. 故障根因分析 | 基于统计数据的根因推断（mod_jk、HTTP 404/403/500） |
| 8. 总结与优化建议 | 问题优先级排序、具体优化措施 |

**要求：** 报告使用 Lesson 1/2 的实际统计数据，根因分析需有独立思考，不能全由 AI 生成。

### 4.5 Lesson 3 验收标准

- [x] `charts/` 下生成 3 张 PNG 图表
- [x] `log_analyzer/` 包结构完整，可独立 import
- [x] `analysis_report.md` 包含完整 8 个章节
- [x] 根因分析基于实际统计数据

### 4.6 提交文件

| 文件 | 说明 |
|------|------|
| `lesson3_可视化与报告.py` | 可视化 + 工具库演示脚本 |
| `log_analyzer/` | 工具库目录 |
| `charts/` | 可视化图表 PNG 文件 |
| `analysis_report.md` | 分析报告 |

---

## 5. AI 开发全流程文档

### 5.1 文档清单

| 文档 | 说明 | 完成时间 |
|------|------|----------|
| `prd.md` | 产品需求文档：项目背景、功能需求、验收标准 | L1 |
| `design.md` | 技术设计文档：架构设计、模块划分、正则设计、数据流 | L1 |
| `dev.md` | 开发文档：环境搭建、代码结构、接口说明、开发日志 | L2 |
| `test-strategy.md` | 测试策略文档：测试方案、测试用例、验证标准 | L3 |
| `ai-log.md` | AI 协作记录：至少 3 条（每课时至少 1 条） | 全程 |

### 5.2 ai-log.md 格式

每条记录包含五个字段：

| 字段 | 说明 |
|------|------|
| **目的** | 这次问 AI 想达成什么？ |
| **输入** | 给 AI 提供了什么材料/约束？ |
| **建议** | AI 给出了什么方案？ |
| **人工判断** | 采纳/修改/拒绝了 AI 的什么建议？为什么？ |
| **验证** | 如何证明最终结果可靠？ |

> **红线：** 人工判断只写"AI说得对"或贴聊天截图 → 该条记录无效。

---

## 6. AI 使用规则

| 规则 | 说明 |
|------|------|
| **允许** | AI 生成代码框架、正则表达式、可视化代码、报告框架 |
| **要求** | 理解代码含义、能解释核心逻辑、逐条校验 AI 输出结果 |
| **禁止** | 不验证就复制 AI 代码、不确认就照搬 AI 输出、报告完全由 AI 生成 |
