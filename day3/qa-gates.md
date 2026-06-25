# 小说 RAG 最小 Demo · QA Gates 质量门禁

## 1. 文档目标

本文件用于定义小说 RAG 最小 Demo 第一阶段的质量门禁。

当前阶段目标是验证：

```
TXT 输入 → 章节切分 → chunk 切分 → chunks.json 输出
```

是否稳定、可复现、可验收。

质量门禁用于决定当前阶段是否可以进入后续阶段：

```
chunks.json → Embedding → FAISS → RAG 问答
```

---

## 2. 当前阶段边界

### 当前阶段包含

- 读取本地 TXT 文件
- 兼容 UTF-8 / GBK / GB18030 编码
- 识别中文网文章节标题
- 按 chunk_size 和 overlap 切分正文
- 生成 chunks.json
- 输出章节数、chunk 数、平均 chunk 长度

### 当前阶段不包含

- Embedding
- FAISS 建库
- 向量检索
- LLM 问答
- Agent 工具调用
- MCP
- Playwright 自动爬取
- 人物关系图谱
- 剧情时间线分析
- 前端页面

---

## 3. Gate 总览

| Gate ID | Gate 名称 | 目标 | 准入条件 | 准出条件 | 失败动作 |
|---------|-----------|------|----------|----------|----------|
| G1 | 需求边界门禁 | 确认只做 TXT 预处理 | PRD、设计文档已编写 | 目标明确、非目标明确、无范围膨胀 | 回退修改文档 |
| G2 | 项目结构门禁 | 确认目录结构完整 | 项目根目录已创建 | 必要文件和目录均存在 | 补充缺失文件/目录 |
| G3 | TXT 读取门禁 | 确认文件读取正常 | TXT 文件存在 | UTF-8/GBK 均可读取，无乱码 | 修复编码逻辑 |
| G4 | 章节识别门禁 | 确认章节正则有效 | load_txt() 可用 | 章节数 > 1，标题正确 | 调整正则表达式 |
| G5 | Chunk 切分门禁 | 确认切分逻辑正确 | 章节列表已生成 | chunk 非空、长度合理、有重叠 | 修复切分逻辑 |
| G6 | JSON 输出门禁 | 确认输出格式正确 | chunks 列表已生成 | JSON 可解析、字段完整 | 修复输出逻辑 |
| G7 | 统计信息门禁 | 确认统计输出正确 | JSON 已生成 | 章节数、chunk 数、平均长度均已输出 | 修复统计逻辑 |
| G8 | 测试记录门禁 | 确认测试用例已执行 | 代码已完成 | P0 用例全部通过 | 修复失败用例 |
| G9 | 文档一致性门禁 | 确认文档与实现一致 | 代码和文档均已完成 | 文档中的函数名、参数、输出与代码一致 | 更新文档或代码 |
| G10 | 阶段放行门禁 | 确认可进入下一阶段 | G1-G9 全部通过 | 所有 Gate 通过，无遗留 P0 问题 | 修复遗留问题 |

---

## 4. G1：需求边界门禁

### 目标

确认当前阶段只做小说 TXT 预处理，不提前扩展到完整 RAG。

### 准入条件

进入开发前必须存在或明确以下文档：

- product-prd.md
- design-options.md
- rag_flow.md
- dev-workflow.md

### 检查项

人工检查：

- PRD 中是否明确当前阶段只做 TXT 切分
- 是否明确不做 Embedding、FAISS、LLM 问答
- 是否把后续功能写成"后续规划"，而不是"当前功能"

### 准出条件

满足以下条件才允许进入代码实现：

- 当前阶段目标清楚
- 非目标明确
- P0 需求没有包含完整 RAG
- 文档没有夸大当前功能

### 失败动作

如果发现范围膨胀：

- 回退修改 product-prd.md
- 回退修改 design-options.md
- 删除或移动不属于当前阶段的功能描述
- 重新执行 G1 检查

---

## 5. G2：项目结构门禁

### 目标

确认项目目录结构满足最小 Demo 要求。

### 准入条件

已经创建项目根目录。

### 自动检查项

检查以下文件或目录是否存在：

- `day3/小说/轮回乐园.txt`
- `day3/split.py`
- `day3/product-prd.md`
- `day3/design-options.md`
- `day3/rag_flow.md`
- `day3/dev-workflow.md`
- `day3/test-strategy.md`
- `day3/qa-gates.md`

### 推荐检查命令

```bash
ls day3/
ls day3/小说/
```

### 准出条件

- 所有必要文件存在
- 无空目录占位

### 失败动作

- 补充缺失文件
- 如果小说文件不存在，确认文件位置并更新路径
- 重新执行 G2 检查

---

## 6. G3：TXT 读取门禁

### 目标

确认 `load_txt()` 函数能正确读取小说文件。

### 准入条件

- TXT 文件存在
- `load_txt()` 函数已实现

### 自动检查项

```bash
python -c "
from split import load_txt
text = load_txt('day3/小说/轮回乐园.txt')
print(f'字符数: {len(text)}')
print(f'前100字: {text[:100]}')
"
```

### 准出条件

- 输出字符数 > 0
- 前 100 字无乱码
- 无 UnicodeDecodeError

### 失败动作

- 如果乱码，检查文件实际编码
- 调整 `load_txt()` 中的编码尝试顺序
- 重新执行 G3 检查

---

## 7. G4：章节识别门禁

### 目标

确认 `detect_chapters()` 函数能正确识别章节标题。

### 准入条件

- `load_txt()` 通过 G3
- `detect_chapters()` 函数已实现

### 自动检查项

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

### 准出条件

- 章节数 > 1（除非原文确实只有 1 章）
- 第 1 章标题包含"第1章"
- 最后 1 章标题包含"第xxx章"
- 无运行时错误

### 失败动作

- 如果章节数为 1，打印前 500 字检查标题格式
- 调整正则表达式
- 重新执行 G4 检查

---

## 8. G5：Chunk 切分门禁

### 目标

确认 `split_chapter()` 函数能正确切分章节内容。

### 准入条件

- 章节列表已通过 G4
- `split_chapter()` 函数已实现

### 自动检查项

```bash
python -c "
from split import load_txt, detect_chapters, split_novel
chunks = split_novel('day3/小说/轮回乐园.txt', chunk_size=500, overlap=100, max_chapters=10)
print(f'Chunk 数: {len(chunks)}')
avg = sum(c['char_count'] for c in chunks) / len(chunks)
print(f'平均长度: {avg:.0f} 字')
empty = [c for c in chunks if c['char_count'] == 0]
print(f'空 chunk 数: {len(empty)}')
"
```

### 准出条件

- Chunk 数 > 章节数
- 平均长度接近 chunk_size（允许 ±20% 偏差）
- 空 chunk 数 = 0
- 相邻 chunk 有重叠内容

### 失败动作

- 如果 Chunk 数等于章节数，检查切分逻辑
- 如果平均长度偏差过大，检查 `_find_split_point()`
- 如果有空 chunk，检查 strip() 逻辑
- 重新执行 G5 检查

---

## 9. G6：JSON 输出门禁

### 目标

确认 `chunks.json` 输出格式正确、可解析。

### 准入条件

- chunks 列表已通过 G5
- JSON 导出逻辑已实现

### 自动检查项

```bash
python -c "
import json
data = json.load(open('day3/轮回乐园_chunks.json', encoding='utf-8'))
print(f'记录数: {len(data)}')
print(f'字段: {list(data[0].keys())}')
required = ['chunk_id', 'chapter_title', 'content', 'char_count']
for r in required:
    assert r in data[0], f'缺少字段: {r}'
print('字段完整性: 通过')
"
```

### 准出条件

- `json.load()` 无报错
- 每条记录包含 chunk_id、chapter_title、content、char_count
- 无空 content

### 失败动作

- 如果 JSON 格式错误，检查 `json.dumps()` 参数
- 如果缺少字段，检查 chunk 构建逻辑
- 重新执行 G6 检查

---

## 10. G7：统计信息门禁

### 目标

确认程序输出正确的统计信息。

### 准入条件

- JSON 已通过 G6

### 自动检查项

运行完整流程，检查命令行输出：

```bash
python day3/split.py "day3/小说/轮回乐园.txt" --max-chapters 300 -o day3/轮回乐园_chunks.json
```

### 准出条件

命令行输出包含：

- 章节数
- Chunk 数
- 平均 Chunk 长度
- 输出文件路径

### 失败动作

- 如果缺少统计信息，检查 `main()` 函数
- 如果数值异常，检查计算逻辑
- 重新执行 G7 检查

---

## 11. G8：测试记录门禁

### 目标

确认测试用例已执行并记录。

### 准入条件

- 代码已完成
- test-strategy.md 已编写

### 检查项

人工检查：

- test-strategy.md 中的 P0 用例是否已执行
- 是否有失败记录
- 失败是否已修复并回归

### 准出条件

- 所有 P0 用例通过
- 无未修复的失败记录
- 回归测试已执行

### 失败动作

- 补充执行未完成的测试用例
- 修复失败用例
- 重新执行回归测试
- 重新执行 G8 检查

---

## 12. G9：文档一致性门禁

### 目标

确认文档与代码实现一致。

### 准入条件

- 代码和文档均已完成

### 检查项

人工检查：

- rag_flow.md 中的函数名是否与代码一致
- product-prd.md 中的数据结构是否与实际输出一致
- dev-workflow.md 中的验证命令是否可执行
- test-strategy.md 中的预期结果是否与实际一致

### 准出条件

- 文档中的函数名、参数、输出与代码一致
- 无过时的文档内容
- 验证命令可直接复制执行

### 失败动作

- 更新文档以匹配代码
- 或更新代码以匹配文档（需评估影响）
- 重新执行 G9 检查

---

## 13. G10：阶段放行门禁

### 目标

确认当前阶段已完成，可以进入下一阶段。

### 准入条件

- G1-G9 全部通过

### 检查项

确认清单：

- [ ] G1 需求边界：无范围膨胀
- [ ] G2 项目结构：文件完整
- [ ] G3 TXT 读取：无乱码、无报错
- [ ] G4 章节识别：章节数合理
- [ ] G5 Chunk 切分：长度合理、有重叠
- [ ] G6 JSON 输出：格式正确、字段完整
- [ ] G7 统计信息：输出正确
- [ ] G8 测试记录：P0 用例全部通过
- [ ] G9 文档一致性：文档与代码一致

### 准出条件

- 所有检查项通过
- 无遗留 P0 问题
- chunks.json 可作为下一阶段输入

### 失败动作

- 定位未通过的 Gate
- 修复对应问题
- 重新执行该 Gate
- 重新执行 G10 检查

---

## 14. QA Gate 与 Harness 区分

### QA Gate

QA Gate 是质量检查点，用于判断是否可以进入下一阶段。

当前项目 QA Gate：

- G1-G10（如上所述）

特点：

- 有明确的准入/准出条件
- 有失败后的回退动作
- 用于阶段放行决策

### Harness

Harness 是测试执行框架，用于自动化运行测试。

当前项目 Harness：

- Python 脚本直接执行
- 命令行验证
- json.load() 验证

特点：

- 用于执行具体测试
- 不做放行决策
- 只报告通过/失败

### 区分说明

| 维度 | QA Gate | Harness |
|------|---------|---------|
| 目的 | 阶段放行决策 | 执行测试 |
| 输出 | 通过/不通过 + 回退动作 | 测试结果 |
| 示例 | G6: JSON 输出门禁 | `python -c "import json; ..."` |
| 时机 | 阶段结束时 | 开发过程中 |

---

## 15. 后续阶段门禁（当前不实现）

### 阶段 2：Embedding 门禁

- 确认 Embedding 模型加载成功
- 确认向量维度正确
- 确认中文文本向量质量

### 阶段 3：FAISS 检索门禁

- 确认索引构建成功
- 确认 top-k 检索结果相关
- 确认检索速度可接受

### 阶段 4：RAG 问答门禁

- 确认回答相关性
- 确认幻觉控制
- 确认来源引用准确性
