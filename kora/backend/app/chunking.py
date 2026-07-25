from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Recursive-ish splitter: prefer paragraph/sentence breaks."""
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    separators = ["\n\n", "\n", "。", "！", "？", ". ", "; ", "；", " "]
    return _split(cleaned, separators, chunk_size, overlap)


def _split(text: str, separators: list[str], chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if not separators:
        step = max(1, chunk_size - overlap)
        return [text[i : i + chunk_size] for i in range(0, len(text), step) if text[i : i + chunk_size].strip()]

    sep = separators[0]
    parts = text.split(sep) if sep else [text]
    chunks: list[str] = []
    buf = ""

    for part in parts:
        candidate = part if not buf else f"{buf}{sep}{part}"
        if len(candidate) <= chunk_size:
            buf = candidate
            continue
        if buf.strip():
            chunks.append(buf.strip())
        if len(part) > chunk_size:
            chunks.extend(_split(part, separators[1:], chunk_size, overlap))
            buf = ""
        else:
            buf = part

    if buf.strip():
        chunks.append(buf.strip())

    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    # Soft overlap: prepend tail of previous chunk when helpful
    overlapped: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        merged = f"{prev_tail}\n{chunks[i]}".strip()
        overlapped.append(merged if len(merged) <= chunk_size + overlap else chunks[i])
    return overlapped
