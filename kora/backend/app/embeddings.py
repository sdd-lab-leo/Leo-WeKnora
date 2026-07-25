from __future__ import annotations

import hashlib
import math
import struct
from typing import Sequence

import httpx

from .config import settings


def _hash_embedding(text: str, dim: int) -> list[float]:
    """Deterministic demo embedding when no model endpoint is available."""
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dim:
        seed = hashlib.sha256(seed).digest()
        for i in range(0, len(seed), 4):
            if len(values) >= dim:
                break
            n = struct.unpack(">I", seed[i : i + 4])[0]
            values.append((n / 0xFFFFFFFF) * 2 - 1)
    return _normalize(values)


def _normalize(vec: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.has_openai:
        return await _embed_openai(texts)
    ollama = await _embed_ollama(texts)
    if ollama is not None:
        return ollama
    return [_hash_embedding(t, settings.embed_dim) for t in texts]


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text]))[0]


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.openai_embed_model, "input": texts}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/embeddings",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        data.sort(key=lambda x: x["index"])
        return [_normalize(item["embedding"]) for item in data]


async def _embed_ollama(texts: list[str]) -> list[list[float]] | None:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            out: list[list[float]] = []
            for text in texts:
                resp = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/embeddings",
                    json={"model": settings.ollama_embed_model, "prompt": text},
                )
                if resp.status_code >= 400:
                    return None
                out.append(_normalize(resp.json()["embedding"]))
            return out
    except Exception:
        return None


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(n))
