"""交互式检索 — 加载 FAISS 索引，输入问题返回 top-k 相关 chunk。"""

import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
STORAGE_DIR = Path(__file__).parent / "storage"
INDEX_PATH = STORAGE_DIR / "faiss.index"
METADATA_PATH = STORAGE_DIR / "metadata.json"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"
TOP_K = 5
MAX_PREVIEW = 500


def load_all():
    for p in (INDEX_PATH, METADATA_PATH, CHUNKS_PATH):
        if not p.exists():
            print(f"错误：找不到 {p}")
            print("请先运行 build_index.py 构建索引")
            sys.exit(1)

    # FAISS C++ 后端不支持 Unicode 路径，先复制到临时文件再读取
    with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as tmp:
        tmp_path = tmp.name
    shutil.copy2(INDEX_PATH, tmp_path)
    try:
        index = faiss.read_index(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # 建立 chunk_id -> content 的映射
    content_map = {c["chunk_id"]: c["content"] for c in chunks}

    return index, metadata, content_map


def search(query: str, model: SentenceTransformer, index, metadata, content_map, top_k: int = TOP_K):
    embedding = model.encode([query], normalize_embeddings=True)
    embedding = np.array(embedding, dtype=np.float32)

    scores, indices = index.search(embedding, top_k)

    results = []
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
        if idx == -1:
            continue
        meta = metadata[idx]
        content = content_map.get(meta["chunk_id"], "")
        results.append({
            "rank": rank,
            "score": score,
            "chunk_id": meta["chunk_id"],
            "chapter_title": meta["chapter_title"],
            "char_count": meta["char_count"],
            "content": content,
        })
    return results


def print_results(results):
    for r in results:
        print("=" * 60)
        print(f"Top {r['rank']}")
        print(f"相似度分数：{r['score']:.4f}")
        print(f"Chunk ID：{r['chunk_id']}")
        print(f"章节标题：{r['chapter_title']}")
        print(f"字符数：{r['char_count']}")
        print()
        preview = r["content"][:MAX_PREVIEW]
        if len(r["content"]) > MAX_PREVIEW:
            preview += "..."
        print("内容预览：")
        print(preview)
    print("=" * 60)


def main():
    # Windows 下 stdin 默认编码可能不是 UTF-8，强制重新配置
    if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")

    print(f"加载模型: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, device=device)

    print("加载索引和 metadata...")
    index, metadata, content_map = load_all()
    print(f"索引包含 {index.ntotal} 个向量，维度 {index.d}")
    print()

    print("输入问题进行检索，输入 exit/quit/q 退出")
    print("-" * 40)

    while True:
        try:
            query = input("\n请输入问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print("退出")
            break

        results = search(query, model, index, metadata, content_map)
        if not results:
            print("未找到相关结果")
            continue
        print()
        print_results(results)


if __name__ == "__main__":
    main()
