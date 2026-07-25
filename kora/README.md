# Kora — Living Knowledge Prototype

A lightweight product prototype inspired by WeKnora's core idea:

**Documents → Retrievable knowledge → Agent reasoning → Self-maintaining Wiki**

Not a fork of WeKnora. A greenfield MVP that keeps only the philosophy and ships as a single local stack.

## What it does

| Mode | Capability |
|------|------------|
| **RAG** | Upload docs → chunk → embed → hybrid search (FTS + vectors) → cited answers |
| **Agent** | ReAct-style loop with a `knowledge_search` tool for multi-step questions |
| **Wiki** | Distill each document into a linked Markdown wiki page |

## Stack

- **Backend**: FastAPI + SQLite (FTS5) + in-process vectors
- **Frontend**: Vite + vanilla TypeScript (single composition UI)
- **Models**: OpenAI-compatible API or Ollama

## Quick start

```bash
cd kora
cp .env.example .env   # set OPENAI_API_KEY or OLLAMA_BASE_URL
make install
make run
```

Open http://localhost:5173

API docs: http://localhost:8000/docs

## Demo without a model key

If no LLM/embedding endpoint is configured, Kora falls back to:

- Hash-based demo embeddings (still searchable)
- Template answers that surface retrieved chunks

Useful for UI / pipeline demos; set real model credentials for quality.

## Project layout

```
kora/
  backend/app/     # ingest, retrieve, rag, agent, wiki
  frontend/        # product UI
  samples/         # sample markdown docs
  data/            # sqlite + uploads (gitignored)
```

## Scope (intentionally small)

**In**: local KB, hybrid RAG, agent tool loop, wiki distill, citations  
**Out**: multi-tenant RBAC, IM connectors, Neo4j, MCP OAuth, task queues, Helm
