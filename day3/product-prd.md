# 小说 RAG 最小 Demo · PRD

## 1. 项目背景

本项目面向长篇中文网文场景。

用户希望将本地 TXT 小说文件转换为后续 RAG 系统可使用的结构化文本块。

当前阶段只做文本预处理，不做完整 RAG。

---

## 2. 用户

- 学生开发者：用于完成课程 Demo / 毕设原型
- 后续 RAG 系统：需要接收结构化 chunks.json 作为输入
- 测试者：需要检查章节切分和 chunk 切分是否正确

---

## 3. 项目目标

实现一个可运行的小说 TXT 预处理 Demo，能够读取本地小说 TXT 文件，识别章节标题，将章节内容切分为固定长度 chunk，并导出包含章节元数据的 chunks.json 文件。

---

## 4. 非目标

当前阶段不实现：

- Embedding
- FAISS 向量索引
- LangChain / LlamaIndex
- LLM 问答
- Agent 工具调用
- 人物关系图谱
- 时间线分析
- 前端页面
- 版权文本来源处理
- 自动爬取小说网站

---

## 5. 功能需求

### P0 必须完成

#### P0-1 读取本地 TXT 文件

**需求描述：**

程序能够从命令行接收 TXT 文件路径，并读取小说全文。

**验收标准：**

运行：

```bash
python split.py data/novel.txt
```

- 程序能够成功读取文件内容
- 如果 UTF-8 读取失败，应尝试 GBK 或 GB18030
- 读取失败时应输出明确错误信息

---

#### P0-2 识别章节标题

**需求描述：**

程序能够识别常见中文网文章节标题。

支持格式包括：

- `第1章 标题`
- `第001章 标题`
- `第一章 标题`
- `第十二章 标题`
- `第123章 标题`

**验收标准：**

- 程序输出章节总数
- 章节数不能为 1，除非原文确实只有 1 章
- 每个章节对象必须包含 `chapter_index`、`chapter_title`、`content`

---

#### P0-3 章节内容切分为 chunk

**需求描述：**

程序能够将每章正文按照固定字符长度切分为 chunk。

默认参数：

- chunk_size = 1000
- overlap = 150

**验收标准：**

- 每个 chunk 的 `text` 字段不能为空
- 大部分 chunk 长度应接近 1000 字
- 相邻 chunk 应存在约 150 字的重叠内容

---

#### P0-4 生成结构化 chunks.json

**需求描述：**

程序能够将切分结果保存为 `storage/chunks.json`。

每条 chunk 数据必须包含：

- `id`
- `chapter_index`
- `chapter_title`
- `chunk_index`
- `text`

**验收标准：**

- 运行结束后存在 `storage/chunks.json`
- JSON 文件可被 Python `json.load()` 正常读取
- 每条记录字段完整

---

#### P0-5 输出统计信息

**需求描述：**

程序运行结束后输出本次处理统计信息。

至少包括：

- 章节数
- Chunk 数
- 平均 Chunk 长度
- 输出文件路径

**验收标准：**

命令行中能看到：

```
章节数：xxx
Chunk数：xxx
平均Chunk长度：xxx
输出文件：storage/chunks.json
```

---

### P1 增强功能

#### P1-1 支持自定义 chunk_size 和 overlap

**需求描述：**

允许用户通过命令行参数指定 chunk_size 和 overlap。

示例：

```bash
python split.py data/novel.txt --chunk-size 800 --overlap 100
```

**验收标准：**

输出 chunk 的平均长度随参数变化。

---

#### P1-2 清洗多余空白

**需求描述：**

清理连续空行、多余空格、网页残留符号等明显噪声。

**验收标准：**

- chunks.json 中不应出现大量连续空行
- 正文内容不应因清洗被大面积删除

---

#### P1-3 保存章节级 JSON

**需求描述：**

除了 chunks.json，也可以额外保存 chapters.json。

**验收标准：**

- `storage/chapters.json` 存在
- 每条记录包含 `chapter_index`、`chapter_title`、`content`

---

### P2 可选功能

#### P2-1 支持超大 TXT 流式处理

**需求描述：**

优化大文件读取，减少内存占用。

**验收标准：**

对于数百 MB TXT 文件，程序不会明显卡死或崩溃。

---

#### P2-2 支持更多章节标题格式

**需求描述：**

支持更复杂章节标题，例如：

- `Chapter 1`
- `正文 第一章`
- `卷一 第1章`

**验收标准：**

提供测试样例，能够正确识别新增格式。

---

#### P2-3 输出切分质量检查报告

**需求描述：**

输出异常章节和异常 chunk，例如：

- 内容为空的章节
- 过短 chunk
- 章节标题异常

**验收标准：**

生成 `storage/split_report.json` 或在命令行中打印异常统计。

---

## 6. 输入与输出

**输入：**

```
data/novel.txt
```

**输出：**

```
storage/chunks.json
```

**可选输出：**

```
storage/chapters.json
storage/split_report.json
```

---

## 7. 数据结构

chunks.json 的目标结构：

```json
{
  "id": "ch1_chunk1",
  "chapter_index": 1,
  "chapter_title": "第1章 猎杀者",
  "chunk_index": 1,
  "text": "正文内容..."
}
```
