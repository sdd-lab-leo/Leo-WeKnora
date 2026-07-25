from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import get_db
from .ingest import make_slug
from .llm import chat_complete


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_wiki_pages() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT w.id, w.slug, w.title, w.document_id, w.updated_at, d.title AS document_title
            FROM wiki_pages w
            JOIN documents d ON d.id = w.document_id
            ORDER BY w.updated_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_wiki_page(slug: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT w.*, d.title AS document_title, d.source_name
            FROM wiki_pages w
            JOIN documents d ON d.id = w.document_id
            WHERE w.slug = ?
            """,
            (slug,),
        ).fetchone()
    return dict(row) if row else None


def _linkify(markdown: str, pages: list[dict[str, Any]], current_slug: str) -> str:
    """Turn bare mentions of other wiki titles into [[slug]] links."""
    out = markdown
    for p in pages:
        if p["slug"] == current_slug:
            continue
        title = p["title"]
        if len(title) < 2:
            continue
        pattern = re.compile(re.escape(title), re.IGNORECASE)
        out = pattern.sub(f"[[{p['slug']}|{title}]]", out, count=1)
    return out


async def distill_wiki(document_id: str) -> dict[str, Any]:
    with get_db() as conn:
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        if not doc:
            raise ValueError("document not found")
        existing = conn.execute(
            "SELECT * FROM wiki_pages WHERE document_id = ?", (document_id,)
        ).fetchone()
        others = conn.execute("SELECT slug, title FROM wiki_pages").fetchall()

    title = doc["title"]
    body = doc["content"][:12000]
    other_titles = ", ".join(r["title"] for r in others if r["title"] != title) or "(none yet)"

    prompt = (
        "Distill the source document into a durable wiki page.\n"
        "Return Markdown with:\n"
        f"# {title}\n"
        "## Summary\n"
        "## Key Points (bullet list)\n"
        "## Concepts\n"
        "## Open Questions\n"
        "Keep it faithful to the source. Mention related pages if relevant "
        f"from this list: {other_titles}.\n\n"
        f"SOURCE:\n{body}"
    )
    markdown = await chat_complete(
        [
            {
                "role": "system",
                "content": "You write crisp internal wiki pages. No preamble.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    slug = existing["slug"] if existing else make_slug(title)
    # ensure unique slug
    if not existing:
        with get_db() as conn:
            clash = conn.execute("SELECT id FROM wiki_pages WHERE slug = ?", (slug,)).fetchone()
            if clash:
                slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    pages_for_links = [{"slug": r["slug"], "title": r["title"]} for r in others]
    pages_for_links.append({"slug": slug, "title": title})
    markdown = _linkify(markdown, pages_for_links, slug)

    now = _now()
    with get_db() as conn:
        if existing:
            conn.execute(
                "UPDATE wiki_pages SET title = ?, markdown = ?, updated_at = ? WHERE id = ?",
                (title, markdown, now, existing["id"]),
            )
            page_id = existing["id"]
        else:
            page_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO wiki_pages (id, document_id, slug, title, markdown, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (page_id, document_id, slug, title, markdown, now, now),
            )

    return {
        "id": page_id,
        "slug": slug,
        "title": title,
        "markdown": markdown,
        "document_id": document_id,
        "updated_at": now,
    }
