Agent mode in Kora

Agent mode is a short ReAct loop, not a full enterprise tool platform.

Available tool

- knowledge_search(query, top_k?): searches the local knowledge base with hybrid retrieval.

Loop

1. The model decides whether it needs evidence.
2. If yes, it emits ACTION: knowledge_search with JSON args.
3. Kora runs the tool and appends an Observation.
4. After enough evidence, the model emits FINAL: with a cited answer.

Why this matters

RAG is ideal for direct lookups. Agent mode helps when the question needs decomposition, multiple retrievals, or synthesis across several documents.

Limitations of the prototype

- One built-in tool only.
- No MCP OAuth, no sandbox skills, no web search by default.
- Max a few steps per question to keep latency predictable.
