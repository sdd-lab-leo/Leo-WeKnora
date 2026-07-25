from __future__ import annotations

import json
import re
from typing import Any

from .llm import chat_complete
from .rag import _save_message
from .retrieval import hybrid_search


TOOL_SPEC = {
    "name": "knowledge_search",
    "description": "Search the local knowledge base with hybrid keyword + vector retrieval.",
    "parameters": {"query": "string search query", "top_k": "optional int, default 5"},
}


def _parse_action(text: str) -> dict[str, Any] | None:
    """Parse a single ReAct action block from model output."""
    # Prefer fenced JSON
    fence = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass

    # ACTION: knowledge_search / FINAL: ...
    if re.search(r"^\s*FINAL\s*:", text, re.IGNORECASE | re.MULTILINE):
        final = re.split(r"FINAL\s*:", text, maxsplit=1, flags=re.IGNORECASE)[1].strip()
        return {"type": "final", "answer": final}

    m = re.search(
        r"ACTION\s*:\s*knowledge_search\s*\nARGS\s*:\s*(\{.*?\})",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        try:
            args = json.loads(m.group(1))
            return {"type": "tool", "name": "knowledge_search", "args": args}
        except json.JSONDecodeError:
            return {"type": "tool", "name": "knowledge_search", "args": {"query": text}}

    # Heuristic: if the model just answers, treat as final
    if "knowledge_search" not in text.lower():
        return {"type": "final", "answer": text.strip()}
    return None


async def agent_answer(session_id: str, question: str, max_steps: int = 3) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    scratch = ""

    system = (
        "You are Kora Agent. Solve questions with a short ReAct loop.\n"
        "You have one tool: knowledge_search(query, top_k?).\n"
        "When you need evidence, output ONLY:\n"
        "ACTION: knowledge_search\n"
        'ARGS: {"query": "...", "top_k": 5}\n'
        "When ready to answer, output ONLY:\n"
        "FINAL: <your answer with [n] citations>\n"
        "Do not invent sources."
    )

    for step_i in range(1, max_steps + 1):
        user_blob = question if step_i == 1 else (
            f"Question: {question}\n\nObservation so far:\n{scratch}\n\nContinue."
        )
        thought = await chat_complete(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user_blob},
            ],
            temperature=0.1,
        )
        action = _parse_action(thought) or {"type": "final", "answer": thought}
        steps.append({"step": step_i, "thought": thought, "action": action})

        if action.get("type") == "final":
            answer = action.get("answer") or thought
            citations = [
                {
                    "chunk_id": e["id"],
                    "document_id": e["document_id"],
                    "document_title": e["document_title"],
                    "ordinal": e["ordinal"],
                    "snippet": e["content"][:280],
                    "score": e.get("score"),
                }
                for e in evidence
            ]
            # de-dupe by chunk id
            seen = set()
            uniq = []
            for c in citations:
                if c["chunk_id"] in seen:
                    continue
                seen.add(c["chunk_id"])
                uniq.append(c)

            _save_message(session_id, "user", question)
            _save_message(session_id, "assistant", answer, citations=uniq, steps=steps)
            return {"answer": answer, "citations": uniq, "steps": steps, "mode": "agent"}

        if action.get("name") == "knowledge_search":
            args = action.get("args") or {}
            query = str(args.get("query") or question)
            top_k = int(args.get("top_k") or 5)
            hits = await hybrid_search(query, top_k=top_k)
            evidence.extend(hits)
            obs_lines = []
            for i, h in enumerate(hits, 1):
                obs_lines.append(
                    f"[{len(evidence) - len(hits) + i}] {h['document_title']}: {h['content'][:400]}"
                )
            observation = "\n".join(obs_lines) if obs_lines else "(no hits)"
            scratch += f"\n\nStep {step_i} search `{query}`:\n{observation}"
            steps[-1]["observation"] = observation
            continue

        # Unknown action → finalize with whatever we have
        break

    # Exhausted steps — force a final answer from evidence
    ctx = scratch or "(no evidence)"
    answer = await chat_complete(
        [
            {
                "role": "system",
                "content": (
                    "Write the best final answer from the evidence. Cite [n] where possible.\n\n"
                    f"Retrieved evidence:\n{ctx}"
                ),
            },
            {"role": "user", "content": question},
        ]
    )
    citations = [
        {
            "chunk_id": e["id"],
            "document_id": e["document_id"],
            "document_title": e["document_title"],
            "ordinal": e["ordinal"],
            "snippet": e["content"][:280],
            "score": e.get("score"),
        }
        for e in evidence
    ]
    _save_message(session_id, "user", question)
    _save_message(session_id, "assistant", answer, citations=citations, steps=steps)
    return {"answer": answer, "citations": citations, "steps": steps, "mode": "agent"}
