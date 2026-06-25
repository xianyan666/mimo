# 中文网文 RAG 最小 Demo

基于《轮回乐园》的中文网文检索增强生成（RAG）最小 demo。

## 当前能力

- 文本切分（章节感知）
- Embedding（BAAI/bge-small-zh-v1.5）
- FAISS 向量索引
- Top-k 检索
- 本地大模型基于证据生成回答（Ollama）

不实现：Agent、LangChain、LlamaIndex、Web UI、多轮记忆。

## 项目结构

```
novel-rag-demo/
├── build_index.py      # 构建 FAISS 索引
├── query.py            # 交互式检索
├── rag_answer.py       # RAG 回答（检索 + 本地大模型）
├── requirements.txt    # Python 依赖
├── README.md
└── storage/
    ├── chunks.json     # 切分后的文本 chunks
    ├── faiss.index     # FAISS 向量索引
    └── metadata.json   # chunk 元数据
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 构建索引

```bash
python build_index.py
```

读取 `storage/chunks.json`，使用 `BAAI/bge-small-zh-v1.5` 生成 embedding，建立 FAISS 内积索引（已 normalize，等价于余弦相似度）。

输出：
- `storage/faiss.index` — FAISS 索引文件
- `storage/metadata.json` — chunk 元数据

## 运行检索

```bash
python query.py
```

交互式命令行，输入问题返回 top-5 相关 chunk。输入 `exit`/`quit`/`q` 退出。

## 技术细节

- Embedding 模型：`BAAI/bge-small-zh-v1.5`（中文，512 维）
- 向量索引：`faiss.IndexFlatIP`（内积，配合 normalize 等价余弦相似度）
- 自动检测 GPU，有 CUDA 则使用 GPU 加速

## RAG 回答

### 1. 启动 Ollama

确保本地已安装 Ollama，并拉取模型：

```bash
ollama pull qwen2.5:7b
```

### 2. 构建索引

```bash
python build_index.py
```

### 3. 运行 RAG 回答

```bash
python rag_answer.py
```

### 4. 示例问题

```text
苏晓第一次进入的世界是什么？他执行了什么任务？
```

当前功能：

- FAISS 检索
- top-k 原文片段召回
- 本地大模型基于片段回答
- 输出来源章节

暂不支持：Agent、MCP、GraphRAG、Web UI、多轮记忆。
