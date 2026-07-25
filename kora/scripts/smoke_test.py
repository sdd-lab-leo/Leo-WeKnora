#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.ingest import ingest_document, list_documents  # noqa: E402
from app.rag import create_session, rag_answer  # noqa: E402
from app.retrieval import hybrid_search  # noqa: E402
from app.wiki import distill_wiki  # noqa: E402


async def main() -> None:
    init_db()
    docs = list_documents()
    if not docs:
        await ingest_document(
            "Smoke Doc",
            "smoke.md",
            "Kora stores knowledge in SQLite and answers with hybrid retrieval.",
        )
        docs = list_documents()

    hits = await hybrid_search("hybrid retrieval", top_k=3)
    assert hits, "expected search hits"
    print(f"search ok: {len(hits)} hits")

    session = create_session("smoke", "rag")
    result = await rag_answer(session["id"], "What does Kora use for storage?")
    assert result["answer"], "expected answer"
    print(f"rag ok: {result['answer'][:120]}...")

    page = await distill_wiki(docs[0]["id"])
    assert page["slug"], "expected wiki slug"
    print(f"wiki ok: {page['slug']}")
    print("SMOKE PASS")


if __name__ == "__main__":
    asyncio.run(main())
