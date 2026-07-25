from __future__ import annotations

from typing import Any

import httpx

from .config import settings


async def chat_complete(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    if settings.has_openai:
        return await _chat_openai(messages, temperature)
    ollama = await _chat_ollama(messages, temperature)
    if ollama is not None:
        return ollama
    return _fallback_answer(messages)


async def _chat_openai(messages: list[dict[str, str]], temperature: float) -> str:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_chat_model,
        "messages": messages,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def _chat_ollama(messages: list[dict[str, str]], temperature: float) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            if resp.status_code >= 400:
                return None
            return resp.json()["message"]["content"].strip()
    except Exception:
        return None


def _fallback_answer(messages: list[dict[str, str]]) -> str:
    """No LLM configured — synthesize a readable demo reply from the last user + context."""
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    ctx = ""
    if "Context:" in system:
        ctx = system.split("Context:", 1)[1].strip()
    elif "Retrieved evidence:" in system:
        ctx = system.split("Retrieved evidence:", 1)[1].strip()

    if not ctx:
        return (
            "（演示模式）未配置可用的 LLM。请在 `.env` 中设置 `OPENAI_API_KEY` "
            "或启动 Ollama。当前没有可引用的检索结果。"
        )

    snippets = [line for line in ctx.splitlines() if line.strip()][:8]
    joined = "\n".join(snippets)
    return (
        f"（演示模式 · 无 LLM）根据检索到的知识片段，与问题「{user}」相关的证据如下：\n\n"
        f"{joined}\n\n"
        "配置真实模型后，这里会生成带推理的自然语言回答。"
    )


def model_status() -> dict[str, Any]:
    return {
        "openai_configured": settings.has_openai,
        "openai_base_url": settings.openai_base_url if settings.has_openai else None,
        "chat_model": settings.openai_chat_model if settings.has_openai else settings.ollama_chat_model,
        "embed_model": settings.openai_embed_model if settings.has_openai else settings.ollama_embed_model,
        "ollama_base_url": settings.ollama_base_url,
        "demo_fallback": True,
    }
