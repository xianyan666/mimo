# ai-log.md

## 1. 总体 AI 使用原则

本项目允许 AI 辅助生成代码框架、正则表达式、统计分析思路、可视化代码和报告结构，但所有结果都需要人工验证。

人工验证包括：

- 抽样检查日志解析结果
- 检查统计结果是否与 CSV 行数一致
- 判断错误类型分类是否合理
- 检查图表是否和统计数据一致
- 报告根因分析结合实际数据修改

---

## 2. Lesson 1 AI 协作记录：日志解析正则设计

| 字段 | 内容 |
|------|------|
| **目的** | 让 AI 辅助设计 Apache 日志解析正则表达式，并决定异常格式行如何处理。 |
| **输入** | 提供 Apache 日志格式 `[时间戳] [日志级别] 日志内容`，以及实际数据中存在 4,478 条无标准前缀日志的情况。 |
| **建议** | AI 建议标准日志用正则提取 timestamp、level、content；非标准日志不要丢弃，标记为 level=unknown。正则使用命名组 `(?P<timestamp>.*?)` 提高可读性。 |
| **人工判断** | 我采纳保留异常行的方案，因为这些行虽然没有标准前缀，但可能包含 `script not found` 等故障信息。如果直接跳过，会导致故障分析证据缺失。命名组方案也采纳，因为 `m.groupdict()` 比编号组更清晰，后续维护更方便。 |
| **验证** | 检查 structured_logs.csv 行数等于原始日志行数（56,482），抽样查看 unknown 行的 content 保留完整，验证标准行 timestamp 非空率为 100%。 |

---

## 3. Lesson 2 AI 协作记录：模块和错误码定义

| 字段 | 内容 |
|------|------|
| **目的** | 让 AI 帮助确定"模块"和"错误码"的定义方式。 |
| **输入** | 提供两种模块理解：Apache 组件前缀和 HTTP 错误大类；提供两种错误码来源：mod_jk state 1~10 和 HTTP 403/404/500。实际数据中 `mod_jk child workerEnv in error state X` 的首词是 mod_jk，但作业要求模块列表包含 workerEnv。 |
| **建议** | AI 建议 module 使用 Apache 组件前缀，error_category 作为请求类/服务类补充分析，error_code 同时纳入 state_X 和 HTTP 状态码。对于 workerEnv，建议优先级高于 mod_jk。 |
| **人工判断** | 我采纳该方案，因为它既符合"按模块筛选"的要求，又能保留 HTTP 错误的分析价值。为了避免概念混乱，我将 module、error_code、error_category 分成三个字段。workerEnv 优先级设定合理，因为 `mod_jk child workerEnv in error state X` 的核心故障组件是 workerEnv 而非 mod_jk 整体。拆分后 workerEnv 独占 4,349 条（11.42%），mod_jk 降至 1,259 条（3.31%），模块粒度更精确。 |
| **验证** | 检查 error_logs.csv 包含 module、error_code、category 字段，error_code_stats.csv 统计数量之和与异常日志总量一致（38,081），module 分布中 workerEnv 和 mod_jk 分开统计。 |

---

## 4. Lesson 3 AI 协作记录：工具包封装和报告生成

| 字段 | 内容 |
|------|------|
| **目的** | 让 AI 帮助设计 log_analyzer/ 工具包结构、图表方案和 analysis_report.md 的生成逻辑。 |
| **输入** | 提供现有根目录模块 log_parser.py、error_filter.py、statistics.py，以及 Lesson 3 要求生成 3 张图表和封装工具包。 |
| **建议** | AI 建议 log_analyzer/ 包自含完整代码，不依赖根目录模块；图表包括每日趋势图、错误码饼图和模块柱状图；报告直接基于统计数据生成 8 个章节。 |
| **人工判断** | 我采纳自含包设计，因为这样 log_analyzer/ 可以独立复用，也不会破坏 Lesson 1/2 已经能运行的脚本。报告部分我会根据实际统计结果补充人工分析，避免只生成模板。根因分析中 mod_jk state 5/6 的含义（后端回复读取失败/连接已关闭）是我根据 Apache mod_jk 文档查阅后补充的，不是 AI 直接给出的。 |
| **验证** | 运行 lesson3_可视化与报告.py，检查 charts/ 中 3 张图是否生成，analysis_report.md 是否包含 8 个章节，并检查报告中的 Top 错误码和 Top 模块是否与统计 CSV 一致。 |
