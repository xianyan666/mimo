# 小说 RAG 最小 Demo · 项目流程图

## 1. 项目目标

本项目是一个面向长篇中文网文的 RAG 最小 Demo。

目标是将本地小说 TXT 文件转换为可检索知识库，并在后续阶段实现基于向量检索的小说内容问答。

当前阶段优先实现文本预处理模块，为后续 Embedding、FAISS 检索和 RAG 问答提供结构化输入。

---

## 2. 当前实现范围

当前只实现：

- 读取本地 TXT 小说文件
- 按章节识别文本结构
- 将章节内容切分为 chunk
- 为 chunk 添加章节信息和序号
- 导出 chunks.json

当前不实现：

- Embedding
- FAISS
- LangChain
- LLM 问答
- Agent 工具调用

---

## 3. 总体流程图

```text
本地小说 TXT 文件
day3/小说/轮回乐园.txt
        |
        v
文本读取
load_txt()
  - 编码检测: UTF-8 -> GBK
  - 返回全文字符串
        |
        v
章节切分
detect_chapters()
  - 正则匹配: 第X章/节/回
  - 输出: [{title, start, end}, ...]
        |
        v
Chunk 切分
split_chapter()
  - 目标长度: 500 字
  - 重叠窗口: 100 字
  - 切分优先级: 段落 > 句号 > 硬切
        |
        v
构建结构化数据
  - chunk_id: "第1章 复仇者_0000"
  - chapter_title: "第1章 复仇者"
  - content: "夜晚时分，一座繁华中..."
  - char_count: 473
        |
        v
导出 JSON
day3/轮回乐园_chunks.json
  - 2174 个 chunks
  - 平均 441 字/chunk
        |
        v
[后续阶段] Embedding 向量化
  - 模型: text2vec / m3e / bge
  - 输入: chunk.content
  - 输出: 768-dim 向量
        |
        v
[后续阶段] FAISS 向量索引
  - 索引类型: IndexFlatIP (内积)
  - 存储: chunks.index + metadata.json
        |
        v
[后续阶段] Top-K 检索
  - 用户提问 -> Embedding -> FAISS 搜索
  - 返回最相关的 K 个 chunks
        |
        v
[后续阶段] LLM 生成回答
  - Prompt: 参考以下小说片段回答问题
  - 输入: Top-K chunks + 用户问题
  - 输出: 自然语言回答
```

---

## 4. 数据流示例

```text
输入: "苏晓的武器是什么?"

[Embedding] -> 向量检索 -> Top-3 chunks:

  1. 第1章 复仇者_0001 (score: 0.87)
     "苏晓，拿起身边的一把长刀，长刀出鞘，刀身乌黑..."

  2. 第1章 复仇者_0003 (score: 0.82)
     "用尽最后力气，苏晓将手中的长刀抛出..."

  3. 第3章 xxx_0002 (score: 0.79)
     "苏晓拔出腰间的长刀，刀身泛着冷光..."

[LLM] -> "苏晓的武器是一把乌黑色的长刀，刀身修长，
          他曾用这把刀完成复仇，并在轮回乐园中继续使用。"
```

---

## 5. 项目结构 (规划)

```
day3/
├── split.py              # [已完成] 文本切分模块
├── rag_flow.md           # [本文档] 流程图说明
├── 小说/
│   └── 轮回乐园.txt      # 原始小说文件
└── 轮回乐园_chunks.json  # [已生成] 切分结果

# 后续扩展
├── embed.py              # [待实现] Embedding 模块
├── index.py              # [待实现] FAISS 索引构建
├── query.py              # [待实现] 检索 + LLM 问答
└── storage/
    ├── chunks.json       # 切分结果
    ├── vectors.npy       # 向量矩阵
    └── index.faiss       # FAISS 索引文件
```
