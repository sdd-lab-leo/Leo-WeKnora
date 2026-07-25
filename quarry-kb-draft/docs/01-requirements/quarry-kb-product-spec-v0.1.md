# Quarry KB Product Specification v0.1

## Document Control

| Field | Value |
|---|---|
| Version | 0.1.5 |
| Status | Draft |
| Layer | Requirements input (`docs/01-requirements/`) |
| Owner | Product owner (TBD) |
| Language | English (per `PROJECT_RULES.md`) |
| Related | `docs/00-context/product-positioning.md`, ADR-0002, `docs/standards/frontend.md`, `docs/standards/backend.md` |
| Prototype | `docs/prototypes/index.html` (mock, no backend) |

This document defines what v0.1 must deliver. It is the upstream input for slice SDD generation. It does not replace slice requirements, spec, architecture, design, or tasks.

### Revision History

| Rev | Change |
|---|---|
| 0.1 | Initial specification |
| 0.1.1 | Resolved D-01 (internal chat gateway), D-02 (OCR in scope), D-03 (no external embedding). |
| 0.1.2 | Resolved D-04 (embedding via internal gateway API) and D-05 (OCR via gateway multimodal). Closed OQ-07 / OQ-08. |
| 0.1.3 | Revised D-01: chat/completion may use the internal gateway **or** configured public OpenAI-compatible providers (e.g. DeepSeek). Embedding and OCR remain intranet-gateway-only. Documented the Ask-time data egress implication. |
| 0.1.4 | Resolved OQ-10 as D-06: multiple public chat providers may be enabled; any authenticated user can switch the chat provider per Ask. |
| 0.1.5 | Added D-07: per-surface degradation when the internal gateway is unavailable (Ask / Upload / Browse). |

---

## 1. Product Positioning

Quarry KB is a department-scale living knowledge workbench for intranet teams (target: one department of about 60 people).

Value chain:

```text
Documents -> Retrievable knowledge -> Cited Q&A -> (later) Agent -> (later) Wiki
```

v0.1 delivers only the first three stages. Agent reasoning and Wiki distillation are deliberately deferred so the team can validate answer quality, ingestion reliability, and daily usefulness first.

Quarry KB is greenfield. It does not fork WeKnora and is not a rebrand of Atlas Knowledge Hub (which targets document conversion and SME review). Quarry KB targets retrieval, answering, and knowledge evolution.

### 1.1 Problem Statement

Department knowledge is scattered across handbooks, process documents, meeting notes, and exported specifications. People re-ask the same questions, answers depend on who is available, and new joiners cannot find authoritative content. Existing wikis are stale and not searchable in a question-oriented way.

### 1.2 v0.1 Product Promise

A colleague can ask a question in natural language and receive an answer that is grounded in uploaded department documents, with visible citations they can open and verify.

### 1.3 Non-Goals For v0.1

Quarry KB v0.1 is not a general chatbot, not a document management system, not a company-wide platform, and not a replacement for the official records system.

---

## 2. Users And Roles

### 2.1 Personas

| Persona | Need |
|---|---|
| Team member (majority) | Ask questions, trust answers, open the source |
| Knowledge maintainer | Upload and curate documents, fix bad parsing |
| Department admin | Manage accounts and roles, watch adoption |
| Pilot sponsor | See whether the tool reduces repeated questions |

### 2.2 Role Capability Matrix

| Capability | Admin | Editor | Viewer |
|---|---|---|---|
| Log in | Yes | Yes | Yes |
| Ask questions and view citations | Yes | Yes | Yes |
| Switch chat provider / model on Ask | Yes | Yes | Yes |
| View own session history | Yes | Yes | Yes |
| Browse knowledge list | Yes | Yes | Yes |
| Open document detail and chunks | Yes | Yes | Read-only |
| Upload documents | Yes | Yes | No |
| Delete documents | Yes | Yes | No |
| Reindex documents | Yes | Yes | No |
| Manage users and roles | Yes | No | No |
| Configure chat providers (incl. public DeepSeek etc.) | Yes | No | No |
| View minimal audit records | Yes | No | No |

Role vocabulary is shared by frontend and backend (`Admin`, `Editor`, `Viewer`) as defined in the standards documents.

---

## 3. Platform Decisions

These decisions are settled and constrain every downstream slice. Each requires an ADR in the destination repository before implementation.

| ID | Decision | Consequence |
|---|---|---|
| D-01 | Chat/completion uses a **configurable OpenAI-compatible provider list**. Supported destinations include the company **internal model gateway** and **public providers** such as DeepSeek (and other Admin-configured OpenAI-compatible endpoints). | The chat adapter is provider-agnostic (`base_url` + API key + model id). An Admin can register providers and choose a system default. Enabling a public chat provider means Ask-time prompts—including retrieved document snippets—may leave the intranet. |
| D-02 | Scanned and image-based documents **are in scope**; OCR is required. | Ingestion needs an OCR-capable parse path, a longer processing budget, per-document parse-mode reporting, and quality expectations that differ from native text. |
| D-03 | Document text **must not** be sent to any external embedding service. | All **embedding** traffic stays inside the intranet perimeter. This does **not** by itself prevent Ask-time snippet egress when a public chat provider is selected (see D-01 warning below). |
| D-04 | Embeddings are produced through the **internal gateway embedding API** (not a locally hosted embedding process on the Quarry host). | Vector dimension is dictated by the gateway embedding model; changing it requires a re-index migration. Compose does not need an on-host embedding container. |
| D-05 | OCR for scanned/image pages is performed through the **internal gateway multimodal** capability (page images or PDFs sent to the gateway OCR/VLM path). | The parse adapter extracts pages, calls the gateway multimodal OCR endpoint, and never uses a public OCR SaaS or a separate on-host OCR stack in v0.1. Gateway latency and multimodal rate limits constrain NFR-04a. |
| D-06 | **Multiple public chat providers** may be enabled at once, and **any authenticated user** (Admin / Editor / Viewer) may switch the chat provider on the Ask screen for each question. | Ask UI includes a provider/model selector listing all enabled providers. The Admin-configured default is preselected for new sessions; the user's last choice may be remembered in the browser/session. Provider credentials stay Admin-only—users only see display names. |
| D-07 | When the **internal model gateway** is unavailable, the product **degrades by surface** instead of going fully offline: **Browse stays fully available**; **Upload still accepts files** but ingest may stall or fail with a clear reason; **Ask keeps history and keyword retrieval**, errors clearly when the selected chat provider is the down gateway (and invites switching to another enabled provider), and never fabricates an answer. | Downstream slices must implement the user-visible states in §6.4. No silent auto-failover of chat provider. Vector search and OCR/embedding ingest depend on the gateway and must surface degraded/failed states. |

### 3.1 Data-egress warning (Ask vs ingest)

| Path | Allowed destinations | What leaves Quarry |
|---|---|---|
| Embedding (ingest) | Internal gateway only (D-03, D-04) | Chunk text → intranet only |
| Multimodal OCR (ingest) | Internal gateway only (D-05) | Page images → intranet only |
| Chat/completion (Ask) | Internal gateway **or** configured public providers (D-01) | User question + **retrieved snippets** → selected provider |

If an Admin enables DeepSeek (or another public chat endpoint), department document excerpts used as RAG context will be sent to that provider during Ask. This is an accepted product trade-off for model quality/flexibility; it must be visible in Admin configuration UX (warning copy), not hidden.

### 3.2 Derived Constraints

- Embedding and OCR remain intranet-gateway-only even when public chat is enabled.
- Chat may egress to the public internet when an Admin enables a public provider **and** a user selects it (or it is the default).
- Multiple public providers may be enabled concurrently (D-06); there is no DeepSeek-only limit.
- The recommended system default for the pilot remains the internal gateway; public providers are Admin opt-in, then user-selectable.
- Users never see or edit API keys; they only choose among enabled provider display names.
- Embedding model id + dimension are configuration values; changing them requires a documented reindex.
- Multimodal OCR work is asynchronous and must not block interactive question answering.
- Provider credentials are stored as secrets; never committed to Git or returned by APIs.
- Internal-gateway outage must not take down Browse; see D-07 and §6.4 for Ask/Upload degradation.

## 4. Scope

### 4.1 In Scope (v0.1)

1. Password-based authentication with JWT sessions; accounts created by an Admin.
2. One department knowledge collection (no multi-workspace, no per-user private collections).
3. Document upload for Markdown, plain text, PDF (including scanned / image-based), and DOCX.
4. Ingestion pipeline with OCR for pages that lack an extractable text layer; status visible as queued, parsing, indexed, or failed.
5. Chunking plus embedding storage in PostgreSQL with pgvector; embeddings from the **internal gateway embedding API** only.
6. Chat/completion via configurable OpenAI-compatible providers (internal gateway and/or public providers such as DeepSeek); embedding and multimodal OCR remain on the **internal gateway** only.
7. Admin configuration of **multiple** chat providers (base URL, API key, model id, enable/disable, system default), with an explicit warning when a public provider is enabled.
8. Ask-time chat provider switcher for all authenticated users (lists enabled providers; remembers last choice when practical).
9. Hybrid retrieval (keyword plus vector) with fused ranking.
10. Answer generation that must include citations to retrieved chunks.
11. Source inspection: open the cited snippet and its parent document.
12. Personal session history (a user sees only their own sessions).
13. Minimal admin surface: user list, role assignment, activate/deactivate, chat-provider settings.
14. Minimal audit trail for upload, delete, reindex, role change, and chat-provider configuration changes.
15. Documented degradation when the internal gateway is unavailable: Browse stays up; Upload accepts then fails ingest clearly; Ask errors or keyword-falls-back without silent provider switch (§6.4).

### 4.2 Out Of Scope (v0.1)

| Deferred item | Reason |
|---|---|
| Agent / ReAct tool loop | Validate grounded answering quality first |
| Wiki distillation and knowledge graph | Depends on stable ingestion and trusted answers |
| Company SSO | Phase 2 per ADR-0002; `external_subject` is reserved from day one |
| Multiple knowledge bases / workspaces | Single department pilot does not need isolation yet |
| IM channels (WeCom, Feishu, Slack) | Web-first validation |
| Website embed widget / public product API keys | No external product integration in pilot |
| Public / third-party providers for **embedding** or **OCR** | Forbidden by D-03 / D-04 / D-05 |
| On-host embedding or OCR containers | Forbidden by D-04 / D-05 for v0.1 |
| Object storage backend (MinIO/S3) | Local disk volume is sufficient for the pilot |
| Streaming token output | Nice to have; not an acceptance blocker for v0.1 |
| Shared or team-visible sessions | Privacy expectations unclear in pilot |
| Per-user free-form entry of arbitrary public model endpoints / API keys | v0.1 limits provider **setup** to Admin-configured entries; users may only **select** among enabled providers |

Deferring an item does not mean designing against it. Public **chat** providers are allowed under D-01; public **embedding/OCR** remain prohibited.

---

## 5. Functional Requirements

Requirement IDs are stable and should be referenced by downstream slice documents.

### 5.1 Authentication And Accounts

| ID | Requirement |
|---|---|
| FR-01 | A user can log in with account identifier and password and receives a session token. |
| FR-02 | Passwords are stored only as hashes; plaintext passwords are never stored or logged. |
| FR-03 | An Admin can create, deactivate, and reactivate accounts. |
| FR-04 | An Admin can assign exactly one role per account from `Admin`, `Editor`, `Viewer`. |
| FR-05 | A deactivated account cannot log in and its existing sessions stop being accepted. |
| FR-06 | The user record reserves an external identity field for later SSO mapping without schema redesign. |
| FR-07 | Authorization is enforced server-side; frontend guards are a usability layer only. |

### 5.2 Knowledge Ingestion

| ID | Requirement |
|---|---|
| FR-10 | An Editor or Admin can upload one or more files of type Markdown, TXT, PDF, or DOCX. |
| FR-11 | The system rejects unsupported types and oversize files with an actionable message. |
| FR-12 | Each uploaded document records title, original filename, type, size, uploader, and upload time. |
| FR-13 | Binary content is stored on a server volume path; the database stores metadata and path only. |
| FR-14 | Ingestion produces text content, chunks, and embeddings for retrieval. |
| FR-14a | When a PDF page has no extractable text layer, the parser sends that page (or document) to the **internal gateway multimodal OCR** path and records that OCR was used for that document (or page range). |
| FR-14b | Embeddings are produced only via the **internal gateway embedding API**; the system never calls a public embedding API and does not run a local embedding server in v0.1. |
| FR-14c | Chat/completion calls are issued through the configured OpenAI-compatible chat provider (internal gateway and/or public providers such as DeepSeek). |
| FR-14d | Chat provider entries, embedding gateway settings, and multimodal OCR path are configuration values. SDKs must not hard-code a single vendor; public chat is opt-in via Admin configuration. |
| FR-14e | An Admin can create, update, disable, and select the system-default chat provider (`name`, `base_url`, `api_key`, `model_id`). Multiple public providers may be enabled at the same time. |
| FR-14f | When saving or enabling a chat provider whose `base_url` is outside the company intranet allowlist, the Admin UI must show a warning that Ask-time retrieved document snippets may leave the intranet. |
| FR-14g | Embedding and OCR configuration accept only intranet gateway endpoints; attempts to point them at public providers are rejected. |
| FR-14h | Any authenticated user can select an enabled chat provider on the Ask screen before sending a question; the selection applies to that Ask (and may persist as the user's preference). |
| FR-14i | The Ask provider selector shows only enabled providers' display names (and optional model label). It never exposes API keys or editable base URLs to non-Admin users. |
| FR-14j | If the user has no stored preference, the system default provider is preselected. If the previously selected provider was disabled, the UI falls back to the system default and notifies the user. |
| FR-15 | Document status is observable as `queued`, `parsing`, `indexed`, or `failed`. |
| FR-16 | A failed document shows a human-readable failure reason (including OCR/parse failures). |
| FR-17 | An Editor or Admin can reindex a document without re-uploading it. |
| FR-18 | An Editor or Admin can delete a document; its chunks and embeddings are removed from retrieval. |
| FR-19 | A user can view a document's metadata, parse mode (native text vs OCR), and a preview of its chunks. |
| FR-20 | The knowledge list supports text search by title and filtering by status. |
| FR-21 | Upload acceptance does not require the internal gateway to be healthy: valid files are stored and a document row is created even when embedding/OCR are unavailable. |
| FR-22 | When ingest cannot complete because the gateway embedding or multimodal OCR path is unavailable, the document ends in `failed` (or remains visibly stalled in `parsing` with a timeout path to `failed`) with a human-readable reason such as "Internal gateway unavailable — retry / reindex later". |
| FR-23 | Browse (knowledge list, document detail, chunk preview, already-indexed content) does not call the internal gateway and remains available during a gateway outage. |

### 5.3 Ask (Retrieval And Answering)

| ID | Requirement |
|---|---|
| FR-30 | Any authenticated user can submit a natural-language question. |
| FR-31 | Retrieval combines keyword matching and vector similarity into a single fused ranking. |
| FR-32 | The answer must cite the chunks it relied on using stable inline markers. |
| FR-33 | Each citation exposes document title, location label (page or chunk ordinal), and a snippet. |
| FR-34 | A user can open a citation to see the fuller source context. |
| FR-35 | When retrieval finds no sufficiently relevant content, the system states that the knowledge base has no basis for an answer instead of producing an unsupported answer. |
| FR-36 | Model or retrieval failures produce a clear error state, not a fabricated answer. |
| FR-37 | Questions and answers are persisted into a session with timestamps. |
| FR-38 | A user can see, reopen, and rename their own sessions. |
| FR-39 | A user cannot read another user's sessions. |
| FR-40 | The Ask interface exposes only RAG mode in v0.1; Agent mode is visible but disabled and clearly labeled as later. |
| FR-41 | Each assistant answer records which chat provider/model generated it (for transparency in the session UI and support debugging). |
| FR-42 | When the selected provider is public, the Ask composer shows a persistent short notice that retrieved snippets may leave the intranet (in addition to the Admin enablement warning). |
| FR-43 | If the selected chat provider is the internal gateway and that gateway is unavailable, Ask shows a clear error with retry and, when other enabled providers exist, a prompt to switch provider. The system must not silently auto-switch providers. |
| FR-44 | If vector retrieval cannot run because the gateway embedding path is unavailable, Ask falls back to **keyword-only retrieval** and shows a short "semantic search unavailable" notice. If keyword retrieval also finds no basis, FR-35 applies. |
| FR-45 | Session list, reopen, and read-only viewing of prior answers remain available during a gateway outage (no new successful answer is required for Browse-of-history). |

### 5.4 Administration And Audit

| ID | Requirement |
|---|---|
| FR-50 | An Admin can list users with role and status. |
| FR-51 | Role changes take effect on the next authorization check. |
| FR-52 | The system records audit entries for upload, delete, reindex, account creation, role change, account status change, and chat-provider create/update/disable/default-change. |
| FR-53 | An audit entry records actor, action, target, and timestamp. |
| FR-54 | Audit records are readable by Admin only in v0.1 (list view is sufficient; no export required). |

---

## 6. Key Flows

### 6.1 Ingest Flow

```text
Editor selects files
  -> validation (type, size)
  -> stored on volume + metadata row created (status: queued)
  -> extract native text
      -> if page/document has no text layer
         -> render page image(s)
         -> gateway multimodal OCR (D-05)
  -> chunk
  -> embed via gateway embedding API (D-04)
  -> index (status: indexed)
```

Failure at any stage sets status `failed` with a reason and keeps the original file for retry. Reindex restarts from parse. Gateway multimodal OCR and embedding calls run in the ingest worker path so interactive Ask traffic is not blocked.

### 6.2 Ask Flow

```text
User question
  -> hybrid retrieval over indexed chunks
  -> relevance check
      -> insufficient  -> "no basis in knowledge base" response (FR-35)
      -> sufficient    -> answer generation via the **selected chat provider** (D-01) with citations
                         (if provider is public: question + retrieved snippets egress)
  -> persist question + answer + citations to session
  -> user can expand sources and open the document
```

### 6.3 Empty And Error States

| State | Expected behavior |
|---|---|
| Knowledge base empty | Ask screen guides the user to ask an Editor to upload content |
| No relevant chunks | Explicit "no basis" answer, no invented content |
| Selected chat provider unavailable | Error banner with retry; question is not silently dropped; if other providers are enabled, invite the user to switch (no silent auto-switch) |
| Gateway embedding unavailable | Ingest fails or times out to `failed` with a clear reason (FR-22); Ask uses keyword-only retrieval with a visible notice (FR-44) |
| Gateway multimodal OCR failed / timed out | Document status `failed` (or partial failure reason); Editor can reindex when the gateway recovers |
| Document parsing failed | Visible failure reason plus reindex action for Editors |
| Permission denied | Non-destructive denial state, no partial data leakage |
| Public chat provider misconfigured / invalid key | Clear Admin-facing and user-facing error; do not fall back silently to another provider without configuration |

### 6.4 Internal-gateway degradation (user-visible)

This section locks what users see when the **internal model gateway** is down or unreachable. "Gateway" here covers the intranet paths used for **chat (when selected)**, **embedding**, and **multimodal OCR**. Public chat providers are independent and may still work.

#### 6.4.1 Per-surface summary

| Surface | Depends on gateway? | Degradation strategy | User-visible outcome |
|---|---|---|---|
| **Browse** (knowledge list, document detail, chunk preview, session history) | No | **No degradation** for already-stored data | Screens load normally. Indexed documents and past answers remain readable. Optional non-blocking notice for Editors/Admins: "Internal gateway unavailable — new OCR/embedding ingest may fail." |
| **Upload** | Yes for ingest completion (embed + OCR); **No** for accepting the file | **Accept then stall/fail** | Upload dialog still works. File is stored; document appears in the list as `queued` → `parsing`, then `failed` with reason if embed/OCR cannot complete. Editor can reindex after recovery. Native-text extract may finish locally, but indexing waits on embedding. Scanned PDFs fail at OCR. |
| **Ask** (new question) | Partial: vector half of hybrid retrieval; chat only if Internal Gateway is selected | **Partial continue + explicit error** | See §6.4.2. Never invent an answer. Never silent provider failover. |

#### 6.4.2 Ask detail (what the user sees)

| Condition | What the user sees | What still works | What does not |
|---|---|---|---|
| Selected provider = **Internal Gateway**, gateway down | Error in the answer area: "Internal gateway is unavailable. Retry, or switch to another enabled model." Retry button + provider selector remain usable. | Session list; prior messages; switching to a public provider | New answer from the internal gateway |
| Selected provider = **public**, gateway down (chat path OK) | Normal answer flow via the public provider. If embedding/vector path is also down: short notice "Semantic search unavailable — using keyword match only." Citations still required when chunks are found. | Ask with keyword retrieval + public chat; Browse | Vector similarity ranking until gateway recovers |
| Selected provider = **public**, but that public provider is also down | Provider-specific error with retry; invite switch to another enabled provider | Browse; other providers if healthy | Answer from the broken provider |
| Gateway down and **no other chat provider** enabled | Same internal-gateway error; no switch option. Copy may say "Ask is unavailable until the gateway recovers or an Admin enables another model." | Browse; Upload accept; session history | New cited answers |
| Retrieval finds nothing (even keyword-only) | FR-35 "no basis" — not a gateway error | — | Fabricated answer |

#### 6.4.3 Upload detail (what the user sees)

| Step | Gateway down? | User-visible state |
|---|---|---|
| Choose files / validation | Irrelevant | Same as healthy: type/size errors only |
| Confirm upload | Irrelevant | Success toast / document row created (`queued`) |
| Native text extract | Usually local — still runs | Status `parsing` |
| OCR (scanned pages) | Required | Stays `parsing` then `failed`: "Internal gateway multimodal OCR unavailable" |
| Embedding | Required | Stays `parsing` then `failed`: "Internal gateway embedding unavailable" |
| After recovery | — | Editor/Admin uses **Reindex** (no re-upload required) |

Upload must not show a blocking "gateway down — cannot upload" that prevents storing the file. A soft banner on Knowledge for Editors is allowed: "Internal gateway unavailable — new documents may fail to index."

#### 6.4.4 Browse detail (what the user sees)

| Action | During gateway outage |
|---|---|
| Open Knowledge list / filter / search by title | Works |
| Open document detail, chunk preview, parse mode, failure reason | Works |
| Open citations from an old answer to a still-indexed document | Works |
| Delete document / change roles / view audit (authorized users) | Works (local app + DB only) |
| Reindex | Allowed to enqueue; will succeed only after gateway recovers (same failure reasons as upload if still down) |

#### 6.4.5 Non-negotiables during outage

1. Do not fabricate answers to hide a gateway failure.
2. Do not silently switch the user's selected chat provider.
3. Do not send embedding or OCR traffic to a public fallback.
4. Do not wipe or hide already-indexed knowledge because the gateway is down.

---

## 7. Domain Concepts

Conceptual model only. Physical schema belongs to slice data-model documents.

| Concept | Purpose | Key attributes (conceptual) |
|---|---|---|
| User | Identity and authorization | identifier, display name, role, status, password hash, reserved external identity |
| Document | Ingested source artifact | title, source filename, type, size, uploader, status, parse mode (`native` / `ocr` / `mixed`), failure reason, timestamps |
| Chunk | Retrievable unit derived from a document | document reference, ordinal, text, location label, embedding (gateway embedding API) |
| Session | A user's conversation container | owner, title, timestamps |
| Message | A question or answer turn | session reference, role, content, timestamp |
| Citation | Link from an answer to a chunk | message reference, chunk reference, marker, snippet |
| Audit Entry | Traceability of sensitive actions | actor, action, target type, target id, timestamp |

---

## 8. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Ten concurrent users asking questions must not cause visible degradation of the web interface. |
| NFR-02 | Target first visible answer content within five seconds under normal latency of the **selected** chat provider. |
| NFR-03 | Maximum single upload size is 50 MB. |
| NFR-04 | A typical native-text document (under 100 pages) reaches `indexed` within five minutes of upload. |
| NFR-04a | A typical OCR document (under 50 pages of scanned content) reaches `indexed` within thirty minutes under normal gateway multimodal latency, without blocking Ask for other users. |
| NFR-05 | The pilot deployment runs on a single intranet host using Docker Compose, with no on-host embedding or OCR containers in v0.1. Egress to public **chat** providers is allowed only when configured; embedding/OCR must not require public egress. |
| NFR-06 | When the internal gateway or the selected chat provider is temporarily unavailable, Browse remains fully usable; Upload still accepts files; Ask follows §6.4 (keyword-only retrieval when vector path is down; clear chat errors without silent provider failover). |
| NFR-07 | Restart of the application must not lose uploaded documents, indexed chunks, or session history. |
| NFR-08 | Backup must be possible by copying the database dump plus the upload volume. |
| NFR-09 | Embedding model identity and vector dimension are configuration values; changing the embedding model requires a documented reindex of affected documents. |

---

## 9. Security And Data Safety

| ID | Requirement |
|---|---|
| SEC-01 | All non-authentication endpoints require a valid session token. |
| SEC-02 | Secrets, tokens, and passwords are never written to logs or returned in API responses. |
| SEC-03 | Uploaded knowledge content never enters the Git repository. |
| SEC-04 | Uploaded filenames are sanitized; path traversal attempts are rejected. |
| SEC-05 | Model prompts must not be logged in full when they contain confidential document text. |
| SEC-06 | Deleting a document removes it from retrieval results immediately. |
| SEC-07 | Answers are treated as assistive output; the product must not present model output as an approved company record (see lesson L-006). |
| SEC-08 | Document text and page images are never sent to public or third-party **embedding** or **OCR** endpoints. |
| SEC-09 | Embedding and OCR base URLs must resolve to intranet/gateway hosts; configuring a public embedding/OCR endpoint is rejected as a configuration error. |
| SEC-10 | Public **chat** providers are allowed only via explicit Admin configuration. Enabling them requires acknowledging that Ask-time retrieved snippets may leave the intranet. |
| SEC-11 | Chat, embedding, and OCR API keys are stored as secrets, never logged, never returned in full by APIs, and never committed to Git. |

---

## 10. Acceptance Criteria

v0.1 is accepted when a live demo on the pilot host satisfies all of the following.

| ID | Acceptance criterion |
|---|---|
| AC-01 | Three accounts exist (Admin, Editor, Viewer) and each role's capability matrix in section 2.2 is observably enforced. |
| AC-02 | A Viewer attempting to upload or delete is denied by the API, not only hidden in the UI. |
| AC-03 | Ten representative department documents are uploaded and all reach `indexed`, or any failure shows an actionable reason. |
| AC-03a | At least one scanned / image-based PDF is uploaded and reaches `indexed` via the OCR path; its parse mode is visible as OCR (or mixed). |
| AC-04 | For ten representative business questions, at least eight answers carry citations that a reviewer confirms as relevant and traceable to the correct document. |
| AC-05 | At least one question with no supporting content returns an explicit "no basis" answer rather than an invented one. |
| AC-06 | A deleted document's content no longer appears in new answers or citations. |
| AC-07 | Reindex recovers a document that previously failed due to a transient error. |
| AC-08 | Session history persists across logout, login, and application restart. |
| AC-09 | Audit list shows entries for upload, delete, reindex, and role change performed during the demo. |
| AC-10 | The system is deployed and started from the documented Compose flow on a single host. |
| AC-11 | With the default (internal-gateway) chat provider, Ask traffic targets the internal gateway; embedding and OCR traffic always target the internal gateway. |
| AC-12 | An Admin can configure **at least two** public OpenAI-compatible chat providers (e.g. DeepSeek and another), keep both enabled, and set one system default. |
| AC-13 | Configuration documents the gateway embedding model id and the gateway multimodal OCR path used in the pilot. |
| AC-14 | Enabling a public chat provider shows the Admin Ask-time data-egress warning; no public key exists for embedding or OCR endpoints. |
| AC-15 | Attempting to point embedding or OCR settings at a public URL is rejected. |
| AC-16 | A Viewer can open Ask, switch between enabled chat providers, and complete a cited question with each selected provider. |
| AC-17 | The answer UI shows which provider/model produced the reply; selecting a public provider shows the short egress notice on the composer. |
| AC-18 | With the internal gateway unreachable and Internal Gateway selected on Ask, the user sees a clear unavailable error with retry and (if configured) a prompt to switch provider; no answer is fabricated and no silent provider switch occurs. |
| AC-19 | With the internal gateway unreachable, Knowledge list and an already-indexed document detail remain fully readable. |
| AC-20 | With the internal gateway unreachable, an Editor can still upload a valid file; the document appears in the list and either stays in a visible ingest state or reaches `failed` with a gateway-unavailable reason; after gateway recovery, reindex can complete without re-upload. |
| AC-21 | With embedding unavailable but a public chat provider selected, Ask either answers using keyword-only retrieval with a visible semantic-search notice, or returns FR-35 when no keyword basis exists. |

---

## 11. Pilot Success Metrics

Adoption signals to review after the pilot period. These are not acceptance gates.

| Metric | Intent |
|---|---|
| Weekly active askers | Whether people return without being reminded |
| Questions per week | Whether it becomes a habit |
| Share of answers where the user opened a citation | Whether citations are trusted and used |
| Documents indexed | Whether maintainers keep feeding it |
| OCR documents indexed successfully | Whether scanned corpus is usable |
| Reported wrong answers | Quality signal for retrieval tuning |

---

## 12. Resolved Decisions And Remaining Open Questions

### 12.1 Resolved (2026-07-25)

| Former ID | Decision | Locked as |
|---|---|---|
| OQ-01 | Chat uses configurable providers: internal gateway **and** public OpenAI-compatible endpoints (e.g. DeepSeek) | D-01 (revised in v0.1.3) |
| OQ-02 | Scanned / image-based PDFs are in scope; **OCR is required** | D-02 |
| OQ-06 | Department document text **must not** be sent to any external embedding service | D-03 |
| OQ-07 | Embeddings use the **internal gateway embedding API** | D-04 |
| OQ-08 | OCR uses the **internal gateway multimodal** path | D-05 |
| OQ-10 | Multiple public chat providers may be enabled; any authenticated user may switch provider on Ask | D-06 |
| OQ-11 | Per-surface degradation when the internal gateway is down (Browse full / Upload accept-then-fail / Ask partial) | D-07 |

### 12.2 Still Open

| ID | Question | Impact if unresolved |
|---|---|---|
| OQ-03 | Which team is the first pilot group and what corpus do they contribute? | Blocks AC-03 / AC-03a / AC-04 test material |
| OQ-04 | Is there a designated company UI component library for intranet apps? | Frontend standards require an ADR before adopting a new kit |
| OQ-05 | Which retention rule applies to session history and audit entries? | Affects data model and later compliance requests |
| OQ-09 | Exact internal-gateway base URL(s), default chat model id, embedding model id, multimodal OCR model/path, and rate-limit expectations | Needed for `.env.example` and adapter smoke tests |

`knowledge-ingest`, `ask-rag`, and `chat-providers` may proceed to SDD design against D-01–D-07. Concrete endpoint identifiers (OQ-09) land in env/Admin setup without changing product scope.

---

## 13. Proposed Slice Decomposition

Downstream slices derived from this specification. Each slice gets its own full SDD chain.

| Order | Slice key | Covers | Primary requirements |
|---|---|---|---|
| 1 | `repo-bootstrap` | Frontend shell, backend health endpoint, database and migration skeleton, Compose, env template for gateway chat/embedding/OCR settings | Enables all others |
| 2 | `auth-password-jwt` | Login, session token, roles, account administration | FR-01 to FR-07, FR-50 to FR-51 |
| 3 | `knowledge-ingest` | Upload, native parse + gateway multimodal OCR, chunk, gateway embedding, status, reindex, delete; upload-accept / ingest-fail during gateway outage | FR-10 to FR-23, FR-14a–d, D-02 to D-05, D-07 |
| 4 | `ask-rag` | Hybrid retrieval, cited answering via user-selected chat provider, sessions, no-basis behavior, provider label, keyword-only fallback and chat errors on gateway outage | FR-30 to FR-45, D-01, D-06, D-07 |
| 4a | `chat-providers` (may merge into auth or ask) | Admin CRUD for multiple chat providers, system default, public-egress warning; Ask selector for all users | FR-14c–j, FR-52, SEC-10/11, D-06 |
| 5 | `audit-minimal` | Audit entries and Admin list view | FR-52 to FR-54 |

Suggested sequencing rationale: authentication before ingestion so uploads have an owner, and ingestion before answering so retrieval has content. Gateway multimodal OCR and gateway embedding are part of `knowledge-ingest`, not separate slices.

---

## 14. Roadmap After v0.1

Not commitments; direction only.

| Candidate | Trigger |
|---|---|
| Company SSO | Pilot expands beyond the first department |
| Agent mode | Users repeatedly ask multi-step questions that single-shot RAG answers poorly |
| Wiki distillation | Corpus stabilizes and maintainers want curated pages |
| Tagging and multiple collections | Corpus outgrows a single flat collection |
| Streaming answers | Perceived latency becomes the main complaint |
| Object storage backend | Deployment moves beyond a single host |

---

## 15. Traceability Notes

- Downstream slice requirements must reference the FR / NFR / SEC / AC / D identifiers used here.
- Changes to scope in section 4, or reversal of D-01 through D-07, require updating this document before the affected slice is implemented.
- Product boundary claims must stay consistent with `docs/00-context/product-positioning.md` and ADR-0002.
- Destination repository should add ADRs for D-01–D-07 before `knowledge-ingest` / `ask-rag` implementation. D-01/D-06 must record that multiple public chat providers are allowed, users may switch on Ask, and Ask-time snippet egress is accepted when a public provider is selected. D-07 must record the Browse / Upload / Ask degradation matrix in §6.4.
