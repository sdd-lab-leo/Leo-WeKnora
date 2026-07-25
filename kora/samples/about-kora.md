What is Kora?

Kora is a lightweight living-knowledge product prototype.

Its core loop is:

1. Ingest documents into a local knowledge base.
2. Chunk and embed them for hybrid retrieval.
3. Answer questions with citations (RAG mode).
4. Use a small ReAct agent that can call knowledge_search.
5. Distill source documents into interlinked wiki pages.

Design principles

- Local-first: SQLite stores documents, FTS5 handles keyword search, vectors live beside the rows.
- Small surface: no multi-tenant RBAC, no IM connectors, no external queue cluster.
- Product feel: brand, one chat surface, knowledge library, and wiki browser.

Hybrid retrieval

Kora fuses BM25 keyword hits from FTS5 with cosine similarity over embeddings using Reciprocal Rank Fusion (RRF). This keeps exact term matches and semantic paraphrases useful at the same time.

When no cloud or Ollama model is configured, Kora still runs with deterministic demo embeddings and template answers so the pipeline can be exercised end-to-end.
