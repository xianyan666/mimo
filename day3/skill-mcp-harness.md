# 小说 RAG 最小 Demo · Skill / MCP / Harness 方案说明

## 1. 文档目标

本文件用于解释小说 RAG 最小 Demo 中 Skill、MCP、Harness 三个概念的边界和作用。

当前项目处于第一阶段，只实现小说 TXT 文本预处理：

```
TXT 输入 → 章节切分 → chunk 切分 → chunks.json 输出
```

因此当前阶段不会真正实现 MCP 服务，也不会实现完整自动化 Harness 系统。

当前阶段重点是：

- 用 Skill 思路规范 AI 如何完成切分任务
- 用简单命令行测试代替完整 Harness
- 为后续 RAG / Agent / MCP 扩展预留结构

---

## 2. 三个概念一句话区分

| 概念 | 一句话定义 | 在项目中的作用 | 当前阶段是否实现 |
|------|------------|----------------|------------------|
| Skill | 可复用的任务执行方法，告诉 AI "遇到某类任务应该怎么做" | 规范如何完成小说 TXT 切分任务 | 使用 Skill 思路，不做成独立插件 |
| MCP | 模型上下文协议，让 AI 通过标准接口连接外部工具和服务 | 后续封装小说检索、章节查询等能力 | 不实现，当前只做本地预处理 |
| Harness | 自动化运行、检查和回归的执行框架 | 后续自动运行切分、Embedding、检索测试 | 只使用轻量命令行验证 |

---

## 3. 当前阶段项目边界

### 当前阶段包含

- 读取本地 TXT 小说
- 自动兼容 UTF-8 / GBK / GB18030 编码
- 识别中文章节标题
- 按 chunk_size 和 overlap 切分文本
- 生成 chunks.json
- 输出统计信息
- 使用 test-strategy.md 和 qa-gates.md 验证结果

### 当前阶段不包含

- MCP Server
- MCP Client
- Embedding
- FAISS
- LLM 问答
- Agent 工具调用
- Playwright 爬取
- 自动追更
- 完整 Harness 平台
- 前端页面

---

## 4. Skill：怎么做

### 4.1 Skill 的作用

Skill 用于把重复任务沉淀成固定流程。

在本项目中，Skill 不是一个独立程序，而是一套开发规则和执行步骤。

它回答的问题是：

- 处理小说 TXT 时应该先做什么？
- 如何识别章节？
- 如何切分 chunk？
- 输出什么格式？
- 如何判断处理成功？

---

### 4.2 当前项目的 Skill 内容

**Skill 名称：** `novel_txt_split_skill`

**适用场景：**

当输入是中文长篇小说 TXT，并且目标是为后续 RAG 构建 chunks.json 时使用。

**输入：**

- 本地 TXT 文件路径
- chunk_size（默认 500）
- overlap（默认 100）

**处理步骤：**

1. 读取 TXT 文件
2. 尝试 UTF-8 编码
3. UTF-8 失败时尝试 GBK
4. GBK 失败时尝试 GB18030
5. 使用章节标题正则识别章节
6. 将每章正文切分为 chunk
7. 为每个 chunk 添加 chunk_id、chapter_title、content、char_count
8. 保存到 chunks.json
9. 输出章节数、chunk 数、平均 chunk 长度

**输出：**

- chunks.json
- 命令行统计信息

**成功标准：**

- chunks.json 存在
- JSON 合法
- 每条 chunk 字段完整
- chunk content 非空

---

### 4.3 Skill 与代码的关系

Skill 是规则，代码是实现。

| 维度 | Skill | 代码 |
|------|-------|------|
| 是什么 | 任务执行规范 | 具体程序 |
| 作用 | 告诉 AI 或开发者怎么做 | 实际执行 |
| 示例 | "先读取文件，再识别章节" | `load_txt()` → `detect_chapters()` |
| 当前阶段 | 定义在本文档中 | `split.py` |

---

## 5. MCP：连接什么

### 5.1 MCP 的作用

MCP（Model Context Protocol）用于让 AI 通过标准接口连接外部工具、文件系统、数据库或服务。

它解决的问题是：

- AI 如何调用外部工具？
- 如何统一工具接口？
- 如何让不同工具可插拔？

---

### 5.2 MCP 在后续 RAG 系统中的应用

后续阶段可以将以下能力封装为 MCP 工具：

| MCP 工具 | 功能 | 输入 | 输出 |
|----------|------|------|------|
| `novel_split` | 小说 TXT 切分 | TXT 文件路径 | chunks.json |
| `novel_embed` | 文本向量化 | chunks.json | vectors.npy |
| `novel_search` | 向量检索 | 用户问题 | top-k chunks |
| `novel_answer` | RAG 问答 | 用户问题 + chunks | 自然语言回答 |
| `novel_character` | 人物查询 | 人物名称 | 相关片段 |
| `novel_timeline` | 时间线查询 | 章节范围 | 事件列表 |

---

### 5.3 当前阶段为什么不实现 MCP

当前阶段只做本地 TXT 预处理，不需要通过 MCP 协议连接外部工具。

原因：

- 输入是本地文件，不需要网络连接
- 处理逻辑是纯 Python，不需要外部服务
- 输出是本地 JSON，不需要远程存储
- 没有多个工具需要统一接口

当前阶段使用 Skill 思路规范流程即可，MCP 留给后续阶段。

---

### 5.4 MCP 后续接入点

当后续阶段需要以下能力时，再接入 MCP：

- 需要让 AI 自动调用切分、检索、问答工具
- 需要多个工具可插拔组合
- 需要统一的工具调用接口
- 需要远程访问小说数据库

---

## 6. Harness：怎么验

### 6.1 Harness 的作用

Harness 是自动化运行、检查和回归的执行框架，用来批量跑测试、收集结果、生成报告。

它解决的问题是：

- 如何自动运行测试？
- 如何收集测试结果？
- 如何判断是否通过？
- 如何做回归测试？

---

### 6.2 当前阶段的轻量 Harness

当前阶段不实现复杂 Harness，使用轻量命令行验证。

**验证方式：**

```bash
# 主流程验证
python day3/split.py "day3/小说/轮回乐园.txt" --max-chapters 300

# JSON 可读性验证
python -c "import json; d=json.load(open('day3/轮回乐园_chunks.json')); print(len(d))"

# 字段完整性验证
python -c "import json; d=json.load(open('day3/轮回乐园_chunks.json')); print(list(d[0].keys()))"
```

**验证清单：**

- [ ] 程序无报错运行
- [ ] 输出章节数 > 1
- [ ] 输出 Chunk 数 > 章节数
- [ ] 平均 Chunk 长度接近目标值
- [ ] chunks.json 可被 json.load() 读取
- [ ] 每条记录字段完整

---

### 6.3 Harness 后续扩展

后续阶段可以实现完整 Harness：

| 阶段 | Harness 功能 |
|------|--------------|
| 阶段 2 | 自动运行 Embedding，检查向量维度 |
| 阶段 3 | 自动构建 FAISS 索引，检查检索结果 |
| 阶段 4 | 自动运行 RAG 问答，检查回答质量 |
| 阶段 5 | 自动运行 Agent 工具调用，检查工具选择 |

---

### 6.4 Harness 与 test-strategy.md 的关系

| 维度 | test-strategy.md | Harness |
|------|------------------|---------|
| 是什么 | 测试计划文档 | 自动化执行框架 |
| 作用 | 定义测什么、怎么测 | 实际执行测试 |
| 当前阶段 | 已编写 | 轻量命令行 |
| 后续阶段 | 持续更新 | 完整自动化 |

---

## 7. 三者在后续 RAG 系统中的组合

### 组合架构

```
用户提问
    |
    v
Agent（调度中心）
    |
    +-- Skill: 判断问题类型
    |   - 剧情问题 → 调用 novel_search
    |   - 人物问题 → 调用 novel_character
    |   - 时间问题 → 调用 novel_timeline
    |
    +-- MCP: 调用对应工具
    |   - novel_search(question) → top-k chunks
    |   - novel_character(name) → 相关片段
    |   - novel_timeline(range) → 事件列表
    |
    +-- Harness: 自动验证
        - 检查检索结果相关性
        - 检查回答质量
        - 记录测试结果
```

### 各阶段组合方式

| 阶段 | Skill | MCP | Harness |
|------|-------|-----|---------|
| 阶段 1（当前） | 定义切分流程 | 不使用 | 命令行验证 |
| 阶段 2 | 定义向量化流程 | 不使用 | 自动检查向量维度 |
| 阶段 3 | 定义检索流程 | 可选接入 | 自动检查检索结果 |
| 阶段 4 | 定义问答流程 | 接入 MCP | 自动检查回答质量 |
| 阶段 5 | 定义 Agent 流程 | MCP 工具组合 | 完整回归测试 |

---

## 8. 当前阶段总结

当前阶段只需要：

- **Skill 思路**：定义在本文档中，规范切分流程
- **轻量 Harness**：命令行验证，不实现复杂框架
- **MCP 预留**：了解概念，不实际接入

当前阶段不需要：

- MCP Server / Client
- 完整 Harness 平台
- Agent 工具调用

当前阶段的核心产出：

- `split.py`（代码实现）
- `chunks.json`（结构化输出）
- 本文档（Skill 规范）
