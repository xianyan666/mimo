"""构建 FAISS 向量索引 — 读取 chunks.json，生成 embedding 并建立索引。"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
STORAGE_DIR = Path(__file__).parent / "storage"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"
INDEX_PATH = STORAGE_DIR / "faiss.index"
METADATA_PATH = STORAGE_DIR / "metadata.json"


def load_chunks(path: Path) -> list[dict]:
    if not path.exists():
        print(f"错误：找不到 {path}")
        print("请先运行 split.py 生成 chunks.json")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_index(chunks: list[dict], model_name: str = MODEL_NAME):
    # 提取文本
    texts = [c["content"] for c in chunks]

    # 自动选择设备
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")

    # 加载模型并生成 embedding
    print(f"加载模型: {model_name}")
    model = SentenceTransformer(model_name, device=device)

    print(f"生成 {len(texts)} 个 chunk 的 embedding...")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=64,
    )
    embeddings = np.array(embeddings, dtype=np.float32)

    # 建立 FAISS 索引（内积，已 normalize 等价于余弦相似度）
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # 保存索引（FAISS C++ 后端不支持 Unicode 路径，先写临时文件再复制）
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        faiss.write_index(index, tmp_path)
        shutil.copy2(tmp_path, INDEX_PATH)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # 保存 metadata（去掉 content 以节省空间，保留检索后回查的能力）
    metadata = []
    for c in chunks:
        metadata.append({
            "chunk_id": c["chunk_id"],
            "chapter_title": c["chapter_title"],
            "char_count": c["char_count"],
        })
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 打印统计
    print()
    print("=" * 20, "索引构建完成", "=" * 20)
    print(f"Chunk 数量：{index.ntotal}")
    print(f"向量维度：{dim}")
    print(f"索引文件：{INDEX_PATH}")
    print(f"Metadata 文件：{METADATA_PATH}")
    print("=" * 54)


def main():
    chunks = load_chunks(CHUNKS_PATH)
    print(f"读取 {len(chunks)} 个 chunks")
    build_index(chunks)


if __name__ == "__main__":
    main()
