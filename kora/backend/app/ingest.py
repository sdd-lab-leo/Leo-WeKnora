from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .chunking import chunk_text
from .config import settings
from .db import dumps, get_db
from .embeddings import embed_texts


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(title: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in title).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return (base or "page")[:80]


def read_upload_text(filename: str, raw: bytes) -> str:
    name = filename.lower()
    if name.endswith((".md", ".txt", ".markdown", ".csv", ".json")):
        return raw.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        # Minimal PDF text extract without heavy deps: keep raw latin fallback notice
        text = raw.decode("latin-1", errors="ignore")
        # Prefer text between stream markers when present; otherwise store notice
        if "stream" in text and len(text) > 200:
            return (
                f"[PDF uploaded: {filename}]\n"
                "This prototype extracts limited text from PDFs without a parser engine. "
                "Prefer Markdown/TXT for best results.\n\n"
                + text[:4000]
            )
        return f"[PDF uploaded: {filename}]\nBinary PDF — convert to Markdown/TXT for better retrieval."
    return raw.decode("utf-8", errors="ignore")


async def ingest_document(title: str, source_name: str, content: str) -> dict[str, Any]:
    doc_id = str(uuid.uuid4())
    chunks = chunk_text(content, settings.chunk_size, settings.chunk_overlap)
    embeddings = await embed_texts(chunks) if chunks else []

    with get_db() as conn:
        conn.execute(
            "INSERT INTO documents (id, title, source_name, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (doc_id, title, source_name, content, _now()),
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            cid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO chunks (id, document_id, ordinal, content, embedding) VALUES (?, ?, ?, ?, ?)",
                (cid, doc_id, i, chunk, dumps(emb)),
            )
            conn.execute(
                "INSERT INTO chunks_fts (content, chunk_id, document_id) VALUES (?, ?, ?)",
                (chunk, cid, doc_id),
            )

    return {
        "id": doc_id,
        "title": title,
        "source_name": source_name,
        "chunk_count": len(chunks),
        "created_at": _now(),
    }


async def ingest_file(filename: str, raw: bytes, title: str | None = None) -> dict[str, Any]:
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    dest = settings.upload_path / f"{uuid.uuid4().hex}_{Path(filename).name}"
    dest.write_bytes(raw)
    text = read_upload_text(filename, raw)
    return await ingest_document(title or Path(filename).stem, filename, text)


def list_documents() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.title, d.source_name, d.created_at,
                   COUNT(c.id) AS chunk_count,
                   EXISTS(SELECT 1 FROM wiki_pages w WHERE w.document_id = d.id) AS has_wiki
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_document(doc_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            return None
        chunks = conn.execute(
            "SELECT id, ordinal, content FROM chunks WHERE document_id = ? ORDER BY ordinal",
            (doc_id,),
        ).fetchall()
    data = dict(row)
    data["chunks"] = [dict(c) for c in chunks]
    return data


def delete_document(doc_id: str) -> bool:
    with get_db() as conn:
        exists = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not exists:
            return False
        conn.execute("DELETE FROM chunks_fts WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM wiki_pages WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    return True


def make_slug(title: str) -> str:
    return _slugify(title)
