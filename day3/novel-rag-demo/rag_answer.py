"""RAG 回答 — 检索 top-k chunk + 调用本地 Ollama 生成基于证据的回答。"""

import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
LLM_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"
TOP_K = 5
MAX_CONTEXT_CHARS = 800
MAX_PREVIEW_CHARS = 300

STORAGE_DIR = Path(__file__).parent / "storage"
INDEX_PATH = STORAGE_DIR / "faiss.index"
METADATA_PATH = STORAGE_DIR / "metadata.json"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"

FIRST_TIME_KEYWORDS = ["第一次", "第一个", "首次", "最早", "一开始"]

PROMPT_TEMPLATE = """请根据给定的小说原文片段回答用户问题。

要求：
1. 只能依据给定片段回答。
2. 如果片段中没有足够信息，请回答"根据当前检索结果无法确定"。
3. 不要编造剧情。
4. 回答要简洁、明确。
5. 回答后列出使用到的来源章节。

【用户问题】
{question}

【小说原文片段】
{context}

【请输出】
回答：
依据：
来源："""


def is_first_time_question(question: str) -> bool:
    return any(kw in question for kw in FIRST_TIME_KEYWORDS)


def extract_chapter_index(chapter_title: str) -> int:
    """从章节标题中提取章节序号，用于排序。序章等返回 0。"""
    m = re.search(r"第(\d+)[章节回]", chapter_title)
    if m:
        return int(m.group(1))
    return 0


def load_embedder():
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")
    model = SentenceTransformer(MODEL_NAME, device=device)
    return model


def load_faiss_index() -> faiss.Index:
    if not INDEX_PATH.exists():
        print(f"错误：找不到 {INDEX_PATH}")
        print("请先运行：python build_index.py")
        sys.exit(1)
    # FAISS C++ 后端不支持 Unicode 路径，先复制到临时文件再读取
    with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as tmp:
        tmp_path = tmp.name
    shutil.copy2(INDEX_PATH, tmp_path)
    try:
        index = faiss.read_index(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return index


def load_metadata() -> list[dict]:
    if not METADATA_PATH.exists():
        print(f"错误：找不到 {METADATA_PATH}")
        print("请先运行：python build_index.py")
        sys.exit(1)
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_content_map() -> dict[str, str]:
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return {c["chunk_id"]: c["content"] for c in chunks}


def encode_query(model: SentenceTransformer, query: str) -> np.ndarray:
    embedding = model.encode([query], normalize_embeddings=True)
    return np.array(embedding, dtype=np.float32)


def search_chunks(
    model: SentenceTransformer,
    index: faiss.Index,
    metadata: list[dict],
    content_map: dict[str, str],
    question: str,
) -> list[dict]:
    is_first = is_first_time_question(question)
    search_k = 30 if is_first else TOP_K

    query_vec = encode_query(model, question)
    scores, indices = index.search(query_vec, search_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        meta = metadata[idx]
        content = content_map.get(meta["chunk_id"], "")
        chapter_idx = extract_chapter_index(meta["chapter_title"])
        results.append({
            "chunk_id": meta["chunk_id"],
            "chapter_title": meta["chapter_title"],
            "chapter_index": chapter_idx,
            "score": float(score),
            "content": content,
        })

    if is_first:
        results.sort(key=lambda x: (x["chapter_index"], -x["score"]))
    else:
        results.sort(key=lambda x: -x["score"])

    return results[:TOP_K]


def build_context(results: list[dict]) -> str:
    parts = []
    for i, r in enumerate(results, 1):
        content = r["content"][:MAX_CONTEXT_CHARS]
        parts.append(
            f"[片段{i}]\n"
            f"章节：{r['chapter_title']}\n"
            f"Chunk ID：{r['chunk_id']}\n"
            f"内容：\n{content}"
        )
    return "\n\n".join(parts)


def build_prompt(question: str, context: str) -> str:
    return PROMPT_TEMPLATE.format(question=question, context=context)


def call_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
    except requests.ConnectionError:
        print("错误：无法连接 Ollama 服务")
        print(f"请先启动 Ollama，并确认 {OLLAMA_URL} 可访问")
        sys.exit(1)

    if resp.status_code != 200:
        body = resp.text
        if "model" in body and "not found" in body:
            print(f"错误：模型 '{LLM_MODEL}' 不存在")
            print(f"请先运行：ollama pull {LLM_MODEL}")
        else:
            print(f"Ollama 返回错误：{resp.status_code}")
            print(body)
        sys.exit(1)

    data = resp.json()
    return data.get("response", "").strip()


def print_answer(question: str, answer: str, results: list[dict]):
    print()
    print("=" * 16, "RAG 回答", "=" * 16)
    print()
    print("问题：")
    print(question)
    print()
    print("回答：")
    print(answer)
    print()
    print("=" * 16, "来源片段", "=" * 16)
    print()
    for i, r in enumerate(results, 1):
        preview = r["content"][:MAX_PREVIEW_CHARS]
        if len(r["content"]) > MAX_PREVIEW_CHARS:
            preview += "..."
        print(f"[{i}] {r['chapter_title']}")
        print(f"Chunk ID：{r['chunk_id']}")
        print(f"相似度：{r['score']:.4f}")
        print(f"内容预览：")
        print(preview)
        print()
    print("=" * 42)


def main():
    # Windows 下 stdin 默认编码可能不是 UTF-8，强制重新配置
    if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

    print("加载 embedding 模型...")
    model = load_embedder()

    print("加载 FAISS 索引...")
    index = load_faiss_index()

    print("加载 metadata...")
    metadata = load_metadata()

    print("加载 chunks 内容...")
    content_map = load_content_map()

    print(f"索引包含 {index.ntotal} 个向量，维度 {index.d}")
    print()
    print("输入问题进行 RAG 回答，输入 exit/quit/q 退出")
    print("-" * 40)

    while True:
        try:
            question = input("\n请输入问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("退出")
            break

        results = search_chunks(model, index, metadata, content_map, question)
        if not results:
            print("未检索到相关片段")
            continue

        context = build_context(results)
        prompt = build_prompt(question, context)
        answer = call_ollama(prompt)
        print_answer(question, answer, results)


if __name__ == "__main__":
    main()
