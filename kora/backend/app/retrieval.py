from __future__ import annotations

from typing import Any

from .db import get_db, loads
from .embeddings import cosine, embed_query


def _rrf_fuse(
    keyword_hits: list[dict[str, Any]],
    vector_hits: list[dict[str, Any]],
    k: int = 60,
) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    payload: dict[str, dict[str, Any]] = {}

    for rank, hit in enumerate(keyword_hits):
        cid = hit["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        payload[cid] = hit
        payload[cid]["keyword_rank"] = rank + 1

    for rank, hit in enumerate(vector_hits):
        cid = hit["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        if cid not in payload:
            payload[cid] = hit
        payload[cid]["vector_rank"] = rank + 1
        payload[cid]["vector_score"] = hit.get("vector_score")

    fused = []
    for cid, score in scores.items():
        item = dict(payload[cid])
        item["score"] = score
        fused.append(item)
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused


async def hybrid_search(query: str, top_k: int = 6) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    with get_db() as conn:
        fts_rows = []
        fts_q = _fts_query(query)
        if fts_q != '""':
            try:
                fts_rows = conn.execute(
                    """
                    SELECT c.id, c.document_id, c.ordinal, c.content, d.title AS document_title,
                           bm25(chunks_fts) AS bm25_score
                    FROM chunks_fts
                    JOIN chunks c ON c.id = chunks_fts.chunk_id
                    JOIN documents d ON d.id = c.document_id
                    WHERE chunks_fts MATCH ?
                    ORDER BY bm25_score
                    LIMIT ?
                    """,
                    (fts_q, top_k * 3),
                ).fetchall()
            except Exception:
                fts_rows = []

        # LIKE fallback helps CJK queries where FTS tokenization is weak
        if not fts_rows:
            like = f"%{query}%"
            fts_rows = conn.execute(
                """
                SELECT c.id, c.document_id, c.ordinal, c.content, d.title AS document_title,
                       0 AS bm25_score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.content LIKE ?
                LIMIT ?
                """,
                (like, top_k * 3),
            ).fetchall()

        all_chunks = conn.execute(
            """
            SELECT c.id, c.document_id, c.ordinal, c.content, c.embedding, d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            """
        ).fetchall()

    keyword_hits = [
        {
            "id": r["id"],
            "document_id": r["document_id"],
            "ordinal": r["ordinal"],
            "content": r["content"],
            "document_title": r["document_title"],
            "bm25_score": r["bm25_score"],
        }
        for r in fts_rows
    ]

    qvec = await embed_query(query)
    vector_scored: list[dict[str, Any]] = []
    for r in all_chunks:
        emb = loads(r["embedding"], [])
        if not emb:
            continue
        score = cosine(qvec, emb)
        vector_scored.append(
            {
                "id": r["id"],
                "document_id": r["document_id"],
                "ordinal": r["ordinal"],
                "content": r["content"],
                "document_title": r["document_title"],
                "vector_score": score,
            }
        )
    vector_scored.sort(key=lambda x: x["vector_score"], reverse=True)
    vector_hits = vector_scored[: top_k * 3]

    fused = _rrf_fuse(keyword_hits, vector_hits)
    return fused[:top_k]


def _fts_query(query: str) -> str:
    tokens = [t for t in query.replace('"', " ").split() if t]
    if not tokens:
        return '""'
    # OR-join keeps recall high for short Chinese/English queries
    return " OR ".join(f'"{t}"' for t in tokens)
