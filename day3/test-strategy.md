# 小说 RAG 最小 Demo · 测试计划

## 1. 测试目标

本测试计划用于验证小说 RAG 最小 Demo 第一阶段是否可复现、可运行、可验收。

当前阶段重点测试：

- TXT 文件读取
- 文本编码兼容
- 章节标题识别
- chunk 切分
- chunks.json 结构完整性
- 统计信息输出
- 异常输入处理

当前阶段不测试：

- Embedding 效果
- FAISS 检索准确率
- LLM 问答质量
- Agent 工具调用
- MCP
- Playwright 爬取
- 前端交互

---

## 2. 测试范围

### 当前阶段测试范围

- `load_txt()`
- `detect_chapters()`
- `split_chapter()`
- `build_chunks()`
- `save_chunks_json()`
- 命令行主流程

### 不在当前阶段测试范围

- 向量化
- 向量检索
- RAG 回答
- 人物关系抽取
- 剧情时间线
- 自动追更
- 网页爬取

---

## 3. 测试环境

- Python 3.10+
- Windows 10 / Windows 11
- PowerShell 或 CMD
- 本地 TXT 小说文件
- 不依赖云服务
- 不依赖外部 API
- 不消耗 ChatGPT Plus 或 API 额度

---

## 4. 测试数据准备

### D1：正常小说 TXT

**文件：** `day3/小说/轮回乐园.txt`

**内容特点：**

- 包含多个章节
- 章节标题格式类似"第1章 标题"
- 每章有正文内容

**用途：** 测试主流程是否能跑通。

---

### D2：小样本文本

**文件：** `day3/data/sample.txt`

**内容：** 至少包含 3 个章节，每章 500 到 1500 字。

**用途：** 快速测试章节切分和 chunk 切分。

---

### D3：不同编码文件

**文件：** `day3/data/sample_gbk.txt`

**内容：** 与 sample.txt 类似，但保存为 GBK 或 GB18030 编码。

**用途：** 测试编码兼容能力。

---

### D4：异常章节格式文本

**文件：** `day3/data/bad_chapter_format.txt`

**内容：** 不使用"第X章"格式，例如只有普通段落。

**用途：** 测试章节识别失败时是否有提示。

---

### D5：空文件

**文件：** `day3/data/empty.txt`

**内容为空。**

**用途：** 测试空输入处理。

---

### D6：不存在的文件路径

**示例：** `day3/data/not_exists.txt`

**用途：** 测试路径错误提示。

---

## 5. 测试类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 正常测试 | 验证主流程能跑通 | 正常 TXT 生成 chunks.json |
| 边界测试 | 验证极端但合理输入 | 空文件、短章节、单章节 |
| 失败测试 | 验证异常是否可复现 | 文件不存在、编码失败 |
| 拒绝测试 | 验证不会做非目标功能 | 要求程序回答小说问题时提示未实现 |
| 回归测试 | 修改后重新运行核心用例 | 修改正则后重跑章节识别 |

---

## 6. 核心测试用例

| 用例ID | 测试类型 | 测试目标 | 固定输入 | 执行命令 | 预期结果 | 优先级 |
|--------|----------|----------|----------|----------|----------|--------|
| TC-001 | 正常测试 | 正常 TXT 主流程 | `day3/小说/轮回乐园.txt` | `python day3/split.py "day3/小说/轮回乐园.txt" --max-chapters 300` | 程序正常结束，生成 chunks.json，输出统计信息 | P0 |
| TC-002 | 正常测试 | 小样本快速测试 | `day3/data/sample.txt` | `python day3/split.py day3/data/sample.txt` | 识别至少 3 个章节，生成非空 chunks.json | P0 |
| TC-003 | 正常测试 | UTF-8 编码读取 | `day3/data/sample_utf8.txt` | `python day3/split.py day3/data/sample_utf8.txt` | UTF-8 文件读取成功，无乱码 | P0 |
| TC-004 | 正常测试 | GBK 编码读取 | `day3/data/sample_gbk.txt` | `python day3/split.py day3/data/sample_gbk.txt` | UTF-8 失败后尝试 GBK，内容正常读取 | P0 |
| TC-005 | 正常测试 | 章节标题识别 | 包含多种标题格式的 sample.txt | `python day3/split.py day3/data/sample.txt` | "第1章"、"第一章"、"第123章"等格式均被识别 | P0 |
| TC-006 | 正常测试 | chunk_size 默认值 | `day3/data/sample.txt` | `python day3/split.py day3/data/sample.txt` | 默认 chunk_size=500，大部分 chunk 接近 500 字 | P0 |
| TC-007 | 正常测试 | overlap 默认值 | `day3/data/sample.txt` | `python day3/split.py day3/data/sample.txt` | 默认 overlap=100，相邻 chunk 存在重叠 | P0 |
| TC-008 | 边界测试 | 自定义参数 | `day3/data/sample.txt` | `python day3/split.py day3/data/sample.txt --chunk-size 800 --overlap 100` | 平均长度接近 800，重叠约 100 字 | P1 |
| TC-009 | 正常测试 | JSON 字段完整性 | 生成的 chunks.json | `python -c "import json; d=json.load(open('chunks.json')); print(list(d[0].keys()))"` | 每条记录包含 chunk_id、chapter_title、content、char_count | P0 |
| TC-010 | 边界测试 | 章节识别失败 | `day3/data/bad_chapter_format.txt` | `python day3/split.py day3/data/bad_chapter_format.txt` | 不崩溃，输出异常提示 | P1 |
| TC-011 | 边界测试 | 空文件处理 | `day3/data/empty.txt` | `python day3/split.py day3/data/empty.txt` | 不崩溃，输出"文件为空"提示 | P1 |
| TC-012 | 失败测试 | 文件不存在 | `day3/data/not_exists.txt` | `python day3/split.py day3/data/not_exists.txt` | 不崩溃，输出文件不存在错误信息 | P0 |
| TC-013 | 拒绝测试 | 非目标功能拒绝 | 用户传入 --ask 参数 | `python day3/split.py day3/data/sample.txt --ask "主角是谁"` | 提示当前阶段只支持切分，不调用 LLM | P1 |
| TC-014 | 回归测试 | 修改正则后重跑 | `day3/data/sample.txt` + `day3/小说/轮回乐园.txt` | 重跑 TC-001、TC-002、TC-005 | 原有章节仍能识别，chunks.json 结构不变 | P0 |

---

## 7. 失败必须可复现

每条失败用例必须记录：

- 测试用例 ID
- 输入文件名
- 执行命令
- 实际输出
- 错误信息
- 是否可以稳定复现
- 修复方式
- 修复后是否回归通过

### 失败记录示例

**用例 ID：** TC-010

**输入文件：** `day3/data/bad_chapter_format.txt`

**执行命令：**

```bash
python day3/split.py day3/data/bad_chapter_format.txt
```

**实际结果：** 章节数：1

**问题判断：** 章节正则未匹配该文件标题格式。

**修复方式：** 补充章节标题正则。

**回归结果：** 重新运行 TC-005、TC-010、TC-014，均通过。

---

## 8. 回归测试策略

### 触发条件

以下情况必须跑回归：

- 修改章节正则表达式
- 修改 chunk 切分逻辑
- 修改编码检测逻辑
- 修改 JSON 输出格式
- 修改命令行参数解析

### 回归用例集

最小回归集（每次修改后必跑）：

```bash
# TC-001: 主流程
python day3/split.py "day3/小说/轮回乐园.txt" --max-chapters 300

# TC-002: 小样本
python day3/split.py day3/data/sample.txt

# TC-005: 章节识别
python day3/split.py day3/data/sample.txt

# TC-009: JSON 完整性
python -c "import json; d=json.load(open('day3/轮回乐园_chunks.json')); print(list(d[0].keys()))"

# TC-012: 文件不存在
python day3/split.py day3/data/not_exists.txt
```

### 回归通过标准

- 所有 P0 用例通过
- 无新增失败
- 输出格式无变化（除非有意修改）

---

## 9. 后续阶段测试计划（当前不实现）

### 阶段 2：Embedding 测试

- 测试 Embedding 模型加载
- 测试向量维度是否正确
- 测试中文文本向量质量

### 阶段 3：FAISS 检索测试

- 测试索引构建
- 测试 top-k 检索结果
- 测试检索速度

### 阶段 4：RAG 问答测试

- 测试回答相关性
- 测试幻觉控制
- 测试来源引用准确性

### 阶段 5：Agent 测试

- 测试工具选择准确性
- 测试多工具协作
- 测试错误恢复
