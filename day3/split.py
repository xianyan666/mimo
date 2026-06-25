"""网文 TXT 预处理工具 — 章节感知切分"""

import argparse
import json
import re
import sys
from pathlib import Path

# 匹配章节标题行: 第X章/节/回 + 可选标题
CHAPTER_RE = re.compile(
    r'^[ \t]*(第[零一二三四五六七八九十百千万\d]+[章节回])(?:\s+.*)?$',
    re.MULTILINE,
)

# 句末标点，用于切分点优先级
_SENTENCE_ENDS = set('。！？…')


def load_txt(file_path: str) -> str:
    """读取 TXT 文件，UTF-8 优先，失败回退 GBK。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    for enc in ('utf-8', 'gbk'):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue

    raise UnicodeDecodeError(
        'fallback', b'', 0, 1,
        f"无法以 UTF-8 或 GBK 解码文件: {file_path}"
    )


def detect_chapters(text: str) -> list[dict]:
    """检测章节边界，返回 [{"title": ..., "start": ..., "end": ...}, ...]。"""
    matches = list(CHAPTER_RE.finditer(text))
    if not matches:
        return [{"title": "全文", "start": 0, "end": len(text)}]

    chapters = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(0).strip()
        chapters.append({"title": title, "start": start, "end": end})

    # 第一个章节前的内容归入"序章"
    if chapters[0]["start"] > 0:
        pre = text[: chapters[0]["start"]].strip()
        if pre:
            chapters.insert(0, {"title": "序章", "start": 0, "end": chapters[0]["start"]})

    return chapters


def _find_split_point(text: str, target: int) -> int:
    """在 target 附近找最佳切分点（段落 > 句号 > 硬切）。"""
    if target >= len(text):
        return len(text)

    # 优先：在 target 前 200 字内找段落边界
    search_start = max(0, target - 200)
    para_pos = text.rfind('\n\n', search_start, target + 50)
    if para_pos != -1:
        return para_pos + 2

    # 其次：在 target 前 100 字内找句末标点
    search_start = max(0, target - 100)
    for i in range(target, search_start - 1, -1):
        if i < len(text) and text[i] in _SENTENCE_ENDS:
            return i + 1

    # 最后硬切
    return target


def split_chapter(title: str, text: str, chunk_size: int, overlap: int) -> list[dict]:
    """将单个章节文本切分为 chunks。"""
    text = text.strip()
    if not text:
        return []

    chunks = []
    pos = 0
    idx = 0

    while pos < len(text):
        end = pos + chunk_size
        if end < len(text):
            end = _find_split_point(text, end)

        content = text[pos:end].strip()
        if content:
            chunks.append({
                "chunk_id": f"{title}_{idx:04d}",
                "chapter_title": title,
                "content": content,
                "char_count": len(content),
            })
            idx += 1

        # 下一段起点 = 当前结尾 - 重叠
        pos = max(end - overlap, pos + 1)

    return chunks


def split_novel(file_path: str, chunk_size: int = 500, overlap: int = 100, max_chapters: int = None) -> list[dict]:
    """主流程：读取 → 检测章节 → 切分 → 返回 chunks。"""
    print(f"[读取] {file_path}")
    text = load_txt(file_path)
    print(f"   文件大小: {len(text):,} 字符")

    print("[检测] 章节...")
    chapters = detect_chapters(text)
    if max_chapters:
        chapters = chapters[:max_chapters]
    print(f"   处理 {len(chapters)} 个章节")

    all_chunks = []
    for ch in chapters:
        ch_text = text[ch["start"]:ch["end"]]
        chunks = split_chapter(ch["title"], ch_text, chunk_size, overlap)
        all_chunks.extend(chunks)

    print(f"[完成] 切分: {len(all_chunks)} 个 chunks")
    return all_chunks


def main():
    parser = argparse.ArgumentParser(description="网文 TXT 章节感知切分工具")
    parser.add_argument("input", help="输入 TXT 文件路径")
    parser.add_argument("--chunk-size", type=int, default=500, help="每个 chunk 的目标字符数 (默认 500)")
    parser.add_argument("--overlap", type=int, default=100, help="相邻 chunk 重叠字符数 (默认 100)")
    parser.add_argument("--max-chapters", type=int, default=None, help="最多处理前 N 个章节")
    parser.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径 (默认: <input>_chunks.json)")
    args = parser.parse_args()

    output = args.output or str(Path(args.input).stem) + "_chunks.json"

    chunks = split_novel(args.input, args.chunk_size, args.overlap, args.max_chapters)

    Path(output).write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[保存] {output}")

    # 统计
    if chunks:
        avg_len = sum(c["char_count"] for c in chunks) / len(chunks)
        max_len = max(c["char_count"] for c in chunks)
        min_len = min(c["char_count"] for c in chunks)
        print(f"[统计] 平均 {avg_len:.0f} 字, 最大 {max_len} 字, 最小 {min_len} 字")


if __name__ == "__main__":
    main()
