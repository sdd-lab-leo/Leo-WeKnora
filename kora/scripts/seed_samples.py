#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.ingest import ingest_document  # noqa: E402


async def main() -> None:
    init_db()
    samples = ROOT / "samples"
    for path in sorted(samples.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        result = await ingest_document(path.stem.replace("-", " ").title(), path.name, text)
        print(f"seeded {result['title']} ({result['chunk_count']} chunks)")


if __name__ == "__main__":
    asyncio.run(main())
