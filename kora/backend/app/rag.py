from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .db import dumps, get_db, loads
from .llm import chat_complete
from .retrieval import hybrid_search


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(title: str = "New chat", mode: str = "rag") -> dict[str, Any]:
    sid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, mode, created_at) VALUES (?, ?, ?, ?)",
            (sid, title, mode, _now()),
        )
    return {"id": sid, "title": title, "mode": mode, "created_at": _now()}


def list_sessions() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, mode, created_at FROM sessions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, citations, steps, created_at
            FROM messages WHERE session_id = ? ORDER BY created_at
            """,
            (session_id,),
        ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["citations"] = loads(item.get("citations"), [])
        item["steps"] = loads(item.get("steps"), [])
        out.append(item)
    return out


def _save_message(
    session_id: str,
    role: str,
    content: str,
    citations: list[dict[str, Any]] | None = None,
    steps: list[dict[str, Any]] | None = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, citations, steps, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                session_id,
                role,
                content,
                dumps(citations or []),
                dumps(steps or []),
                _now(),
            ),
        )


async def rag_answer(session_id: str, question: str, top_k: int = 6) -> dict[str, Any]:
    hits = await hybrid_search(question, top_k=top_k)
    citations = [
        {
            "chunk_id": h["id"],
            "document_id": h["document_id"],
            "document_title": h["document_title"],
            "ordinal": h["ordinal"],
            "snippet": h["content"][:280],
            "score": h.get("score"),
        }
        for h in hits
    ]

    context_blocks = []
    for i, h in enumerate(hits, 1):
        context_blocks.append(
            f"[{i}] ({h['document_title']} · chunk {h['ordinal']})\n{h['content']}"
        )
    context = "\n\n".join(context_blocks) if context_blocks else "(no retrieved chunks)"

    system = (
        "You are Kora, a precise knowledge assistant. Answer using only the Context. "
        "Cite sources as [n]. If evidence is insufficient, say so clearly.\n\n"
        f"Context:\n{context}"
    )
    answer = await chat_complete(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]
    )

    _save_message(session_id, "user", question)
    _save_message(session_id, "assistant", answer, citations=citations)
    return {"answer": answer, "citations": citations, "mode": "rag"}
