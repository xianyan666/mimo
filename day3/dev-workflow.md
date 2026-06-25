# 小说 RAG 最小 Demo · 开发工作流

## 1. 工作流目标

本工作流用于指导小说 RAG 最小 Demo 第一阶段的开发。

当前阶段目标是：

将本地中文网文 TXT 文件处理为结构化 chunks.json，为后续 Embedding、FAISS 检索和 RAG 问答提供输入。

当前不实现：

- Embedding
- FAISS
- LLM 问答
- Agent
- MCP
- Playwright 爬取
- 前端页面

---

## 2. 开发原则

### 原则 1：先确认需求，再写代码

开发前必须阅读：

- product-prd.md
- design-options.md
- rag_flow.md

确认当前阶段只做 TXT 切分。

### 原则 2：每一步都必须可验证

不能只写"完成代码"，必须有运行命令和检查结果。

### 原则 3：先跑通最小链路，再做增强

优先完成：

```
TXT 输入 → 章节切分 → chunk 切分 → chunks.json 输出
```

不要提前做完整 RAG。

### 原则 4：风险前置

在实现前和 Review 前都要标注风险，例如章节识别失败、编码失败、chunk 断裂等。

---

## 3. 输入与输出

### 输入文件

- `day3/小说/轮回乐园.txt`
- `day3/product-prd.md`
- `day3/design-options.md`
- `day3/rag_flow.md`

### 输出文件

- `day3/split.py`
- `day3/轮回乐园_chunks.json`
- `day3/dev-workflow.md`
- `day3/learning-record.md`
- `day3/test-record.md`

---

## 4. 开发任务拆分

### T1：准备项目结构

**输入：** 项目根目录

**操作：** 确认目录结构：

```
day3/
├── 小说/
│   └── 轮回乐园.txt
├── split.py
├── product-prd.md
├── design-options.md
├── rag_flow.md
├── dev-workflow.md
├── learning-record.md
└── test-record.md
```

**输出：** 目录结构确认完成。

**验证命令：**

```bash
ls day3/
ls day3/小说/
```

**预期结果：** 文件和目录存在，无报错。

**失败路径：** 如果目录不存在，手动创建；如果小说文件不存在，确认文件位置。

---

### T2：实现 load_txt() 函数

**输入：** `day3/小说/轮回乐园.txt`

**操作：**

1. 实现文件读取函数
2. 优先 UTF-8 解码
3. 失败时回退 GBK
4. 仍失败则报错并提示

**输出：** `load_txt()` 函数可用，返回小说全文字符串。

**验证命令：**

```bash
python -c "
from split import load_txt
text = load_txt('day3/小说/轮回乐园.txt')
print(f'读取成功，字符数: {len(text)}')
print(f'前100字: {text[:100]}')
"
```

**预期结果：**

- 输出 `读取成功，字符数: xxx`
- 前 100 字无乱码

**AI 参与点：** AI 辅助编写 UTF-8/GBK 回退逻辑。

**风险：** 编码检测失败导致乱码。

**失败路径：**

- 如果乱码，检查文件实际编码（`file -i filename`）
- 如果文件过大导致内存不足，考虑流式读取（P2）

---

### T3：实现 detect_chapters() 函数

**输入：** `load_txt()` 返回的全文字符串

**操作：**

1. 编写章节正则表达式
2. 匹配 `第X章/节/回` 格式
3. 返回章节列表 `[{title, start, end}, ...]`

**输出：** 章节列表。

**验证命令：**

```bash
python -c "
from split import load_txt, detect_chapters
text = load_txt('day3/小说/轮回乐园.txt')
chapters = detect_chapters(text)
print(f'章节数: {len(chapters)}')
print(f'第1章: {chapters[0][\"title\"]}')
print(f'最后1章: {chapters[-1][\"title\"]}')
"
```

**预期结果：**

- 章节数 > 1（除非原文确实只有 1 章）
- 第 1 章标题包含"第1章"
- 最后 1 章标题包含"第xxx章"

**AI 参与点：** AI 辅助编写正则表达式，覆盖 `第1章`、`第一章`、`第123章` 等格式。

**风险：** 章节标题格式不匹配导致章节数为 1。

**失败路径：**

- 如果章节数为 1，打印前 500 字检查标题格式
- 调整正则表达式后重试

---

### T4：实现 split_chapter() 和 build_chunks()

**输入：** 章节列表

**操作：**

1. 对每个章节按 chunk_size 切分
2. 相邻 chunk 保留 overlap 重叠
3. 切分点优先选段落边界、句末标点
4. 构建结构化数据，包含 chunk_id、chapter_title、content、char_count

**输出：** chunks 列表。

**验证命令：**

```bash
python -c "
from split import load_txt, detect_chapters, split_novel
chunks = split_novel('day3/小说/轮回乐园.txt', chunk_size=500, overlap=100, max_chapters=10)
print(f'Chunk 数: {len(chunks)}')
avg = sum(c['char_count'] for c in chunks) / len(chunks)
print(f'平均长度: {avg:.0f} 字')
print(f'第1个 chunk: {chunks[0][\"chunk_id\"]}, {chunks[0][\"char_count\"]}字')
print(f'第2个 chunk: {chunks[1][\"chunk_id\"]}, {chunks[1][\"char_count\"]}字')
"
```

**预期结果：**

- Chunk 数 > 章节数
- 平均长度接近 chunk_size
- 相邻 chunk 有重叠内容

**AI 参与点：** AI 辅助编写滑窗切分逻辑和切分点优先级判断。

**风险：** chunk 语义断裂。

**失败路径：**

- 如果平均长度远小于 chunk_size，检查切分逻辑
- 如果 chunk 为空，检查章节内容是否正确提取

---

### T5：实现 main() 和 CLI 入口

**输入：** 命令行参数

**操作：**

1. 使用 argparse 解析参数
2. 调用 split_novel() 完成切分
3. 导出 chunks.json
4. 输出统计信息

**输出：** `day3/轮回乐园_chunks.json`

**验证命令：**

```bash
python day3/split.py "day3/小说/轮回乐园.txt" --max-chapters 300 -o day3/轮回乐园_chunks.json
```

**预期结果：**

- 程序无报错
- 输出章节数、Chunk 数、平均长度、输出文件路径
- `day3/轮回乐园_chunks.json` 文件存在

**验证 JSON 可读性：**

```bash
python -c "
import json
data = json.load(open('day3/轮回乐园_chunks.json', encoding='utf-8'))
print(f'记录数: {len(data)}')
print(f'字段: {list(data[0].keys())}')
"
```

**预期结果：**

- `json.load()` 无报错
- 每条记录包含 chunk_id、chapter_title、content、char_count

**AI 参与点：** AI 辅助编写 argparse 配置和统计输出。

**风险：** JSON 文件过大导致打开缓慢。

**失败路径：**

- 如果 JSON 格式错误，检查 json.dumps 参数
- 如果文件过大，使用 `--max-chapters` 限制章节数测试

---

### T6：端到端验证

**输入：** 完整的 split.py 和小说 TXT

**操作：** 运行完整流程，检查输出。

**验证命令：**

```bash
python day3/split.py "day3/小说/轮回乐园.txt" --max-chapters 300 -o day3/轮回乐园_chunks.json
```

**验收清单：**

- [ ] 程序无报错运行
- [ ] 输出章节数 > 1
- [ ] 输出 Chunk 数 > 章节数
- [ ] 平均 Chunk 长度接近 500 字
- [ ] chunks.json 可被 json.load() 读取
- [ ] 每条记录字段完整
- [ ] 前 3 条 chunk 内容无乱码

**风险：** 端到端运行时发现前面步骤遗漏的问题。

**失败路径：**

- 回溯到具体函数（T2/T3/T4）单独验证
- 修复后重新运行 T6

---

## 5. 时间规划（30 分钟）

| 任务 | 预计时间 | 累计时间 |
|------|----------|----------|
| T1 准备项目结构 | 2 分钟 | 2 分钟 |
| T2 实现 load_txt() | 5 分钟 | 7 分钟 |
| T3 实现 detect_chapters() | 5 分钟 | 12 分钟 |
| T4 实现 split_chapter() + build_chunks() | 8 分钟 | 20 分钟 |
| T5 实现 main() 和 CLI | 3 分钟 | 23 分钟 |
| T6 端到端验证 | 5 分钟 | 28 分钟 |
| 缓冲时间 | 2 分钟 | 30 分钟 |

---

## 6. Review 检查点

### Review 前风险标注

| 风险 | 影响 | 控制措施 |
|------|------|----------|
| 章节识别失败 | 章节数为 1 | 打印前 500 字检查标题格式，调整正则 |
| 编码读取失败 | 乱码或报错 | 依次尝试 UTF-8、GBK、GB18030 |
| chunk 语义断裂 | 首尾句子被截断 | 使用 overlap 缓解 |
| JSON 过大 | 打开缓慢 | 优先机器可读，抽样检查 |

### Review 清单

- [ ] 代码能无报错运行
- [ ] 输出 chunks.json 字段完整
- [ ] 章节数合理（> 1）
- [ ] Chunk 数合理（> 章节数）
- [ ] 平均 Chunk 长度接近目标值
- [ ] 无乱码
- [ ] 统计信息输出正确

---

## 7. 失败路径速查

| 失败现象 | 可能原因 | 排查方法 |
|----------|----------|----------|
| UnicodeDecodeError | 编码不对 | 检查文件编码，调整 load_txt() |
| 章节数为 1 | 正则不匹配 | 打印前 500 字，检查标题格式 |
| Chunk 数等于章节数 | 切分逻辑有误 | 检查 chunk_size 是否大于章节长度 |
| 平均长度远小于目标 | 切分点判断异常 | 检查 _find_split_point() 逻辑 |
| JSON 解析失败 | 输出格式错误 | 检查 json.dumps() 参数 |
| 程序卡死 | 文件过大 | 使用 --max-chapters 限制测试 |

---

## 8. 后续阶段（当前不实现）

### 阶段 2：Embedding 向量化

将 chunks.json 中的 text 转换为向量。

### 阶段 3：FAISS 检索

建立 FAISS 索引，支持 top-k 检索。

### 阶段 4：RAG 问答

将检索结果和用户问题拼接成 Prompt，调用 LLM 生成回答。

### 阶段 5：Agent 扩展

根据问题类型选择不同工具。
