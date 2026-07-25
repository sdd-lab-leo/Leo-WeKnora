# Quarry KB Product Specification v0.1

## Document Control

| Field | Value |
|---|---|
| Version | 0.1 |
| Status | Draft |
| Layer | Requirements input (`docs/01-requirements/`) |
| Owner | Product owner (TBD) |
| Language | English (per `PROJECT_RULES.md`) |
| Related | `docs/00-context/product-positioning.md`, ADR-0002, `docs/standards/frontend.md`, `docs/standards/backend.md` |
| Prototype | `docs/prototypes/index.html` (mock, no backend) |

This document defines what v0.1 must deliver. It is the upstream input for slice SDD generation. It does not replace slice requirements, spec, architecture, design, or tasks.

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
| View own session history | Yes | Yes | Yes |
| Browse knowledge list | Yes | Yes | Yes |
| Open document detail and chunks | Yes | Yes | Read-only |
| Upload documents | Yes | Yes | No |
| Delete documents | Yes | Yes | No |
| Reindex documents | Yes | Yes | No |
| Manage users and roles | Yes | No | No |
| View minimal audit records | Yes | No | No |

Role vocabulary is shared by frontend and backend (`Admin`, `Editor`, `Viewer`) as defined in the standards documents.

---

## 3. Scope

### 3.1 In Scope (v0.1)

1. Password-based authentication with JWT sessions; accounts created by an Admin.
2. One department knowledge collection (no multi-workspace, no per-user private collections).
3. Document upload for Markdown, plain text, PDF, and DOCX.
4. Ingestion pipeline with visible status: queued, parsing, indexed, failed.
5. Chunking plus embedding storage in PostgreSQL with pgvector.
6. Hybrid retrieval (keyword plus vector) with fused ranking.
7. Answer generation that must include citations to retrieved chunks.
8. Source inspection: open the cited snippet and its parent document.
9. Personal session history (a user sees only their own sessions).
10. Minimal admin surface: user list, role assignment, activate/deactivate.
11. Minimal audit trail for upload, delete, reindex, and role change.

### 3.2 Out Of Scope (v0.1)

| Deferred item | Reason |
|---|---|
| Agent / ReAct tool loop | Validate grounded answering quality first |
| Wiki distillation and knowledge graph | Depends on stable ingestion and trusted answers |
| Company SSO | Phase 2 per ADR-0002; `external_subject` is reserved from day one |
| Multiple knowledge bases / workspaces | Single department pilot does not need isolation yet |
| IM channels (WeCom, Feishu, Slack) | Web-first validation |
| Website embed widget, public API keys | No external integration in pilot |
| OCR for scanned PDFs | Pending decision OQ-02 |
| Object storage backend (MinIO/S3) | Local disk volume is sufficient for the pilot |
| Streaming token output | Nice to have; not an acceptance blocker for v0.1 |
| Shared or team-visible sessions | Privacy expectations unclear in pilot |

Deferring an item does not mean designing against it. Data model and adapter boundaries must not block these items later.

---

## 4. Functional Requirements

Requirement IDs are stable and should be referenced by downstream slice documents.

### 4.1 Authentication And Accounts

| ID | Requirement |
|---|---|
| FR-01 | A user can log in with account identifier and password and receives a session token. |
| FR-02 | Passwords are stored only as hashes; plaintext passwords are never stored or logged. |
| FR-03 | An Admin can create, deactivate, and reactivate accounts. |
| FR-04 | An Admin can assign exactly one role per account from `Admin`, `Editor`, `Viewer`. |
| FR-05 | A deactivated account cannot log in and its existing sessions stop being accepted. |
| FR-06 | The user record reserves an external identity field for later SSO mapping without schema redesign. |
| FR-07 | Authorization is enforced server-side; frontend guards are a usability layer only. |

### 4.2 Knowledge Ingestion

| ID | Requirement |
|---|---|
| FR-10 | An Editor or Admin can upload one or more files of type Markdown, TXT, PDF, or DOCX. |
| FR-11 | The system rejects unsupported types and oversize files with an actionable message. |
| FR-12 | Each uploaded document records title, original filename, type, size, uploader, and upload time. |
| FR-13 | Binary content is stored on a server volume path; the database stores metadata and path only. |
| FR-14 | Ingestion produces text content, chunks, and embeddings for retrieval. |
| FR-15 | Document status is observable as `queued`, `parsing`, `indexed`, or `failed`. |
| FR-16 | A failed document shows a human-readable failure reason. |
| FR-17 | An Editor or Admin can reindex a document without re-uploading it. |
| FR-18 | An Editor or Admin can delete a document; its chunks and embeddings are removed from retrieval. |
| FR-19 | A user can view a document's metadata and a preview of its chunks. |
| FR-20 | The knowledge list supports text search by title and filtering by status. |

### 4.3 Ask (Retrieval And Answering)

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

### 4.4 Administration And Audit

| ID | Requirement |
|---|---|
| FR-50 | An Admin can list users with role and status. |
| FR-51 | Role changes take effect on the next authorization check. |
| FR-52 | The system records audit entries for upload, delete, reindex, account creation, role change, and account status change. |
| FR-53 | An audit entry records actor, action, target, and timestamp. |
| FR-54 | Audit records are readable by Admin only in v0.1 (list view is sufficient; no export required). |

---

## 5. Key Flows

### 5.1 Ingest Flow

```text
Editor selects files
  -> validation (type, size)
  -> stored on volume + metadata row created (status: queued)
  -> parse to text
  -> chunk
  -> embed
  -> index (status: indexed)
```

Failure at any stage sets status `failed` with a reason and keeps the original file for retry. Reindex restarts from parse.

### 5.2 Ask Flow

```text
User question
  -> hybrid retrieval over indexed chunks
  -> relevance check
      -> insufficient  -> "no basis in knowledge base" response (FR-35)
      -> sufficient    -> answer generation with citations
  -> persist question + answer + citations to session
  -> user can expand sources and open the document
```

### 5.3 Empty And Error States

| State | Expected behavior |
|---|---|
| Knowledge base empty | Ask screen guides the user to ask an Editor to upload content |
| No relevant chunks | Explicit "no basis" answer, no invented content |
| Model endpoint unavailable | Error banner with retry; question is not silently dropped |
| Document parsing failed | Visible failure reason plus reindex action for Editors |
| Permission denied | Non-destructive denial state, no partial data leakage |

---

## 6. Domain Concepts

Conceptual model only. Physical schema belongs to slice data-model documents.

| Concept | Purpose | Key attributes (conceptual) |
|---|---|---|
| User | Identity and authorization | identifier, display name, role, status, password hash, reserved external identity |
| Document | Ingested source artifact | title, source filename, type, size, uploader, status, failure reason, timestamps |
| Chunk | Retrievable unit derived from a document | document reference, ordinal, text, location label, embedding |
| Session | A user's conversation container | owner, title, timestamps |
| Message | A question or answer turn | session reference, role, content, timestamp |
| Citation | Link from an answer to a chunk | message reference, chunk reference, marker, snippet |
| Audit Entry | Traceability of sensitive actions | actor, action, target type, target id, timestamp |

---

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Ten concurrent users asking questions must not cause visible degradation of the web interface. |
| NFR-02 | Target first visible answer content within five seconds under normal model gateway latency. |
| NFR-03 | Maximum single upload size is 50 MB. |
| NFR-04 | A typical text-based document (under 100 pages) reaches `indexed` within five minutes of upload. |
| NFR-05 | The pilot deployment runs on a single intranet host using Docker Compose. |
| NFR-06 | The system remains usable when the LLM endpoint is temporarily unavailable: browsing knowledge and reading documents must still work. |
| NFR-07 | Restart of the application must not lose uploaded documents, indexed chunks, or session history. |
| NFR-08 | Backup must be possible by copying the database dump plus the upload volume. |

---

## 8. Security And Data Safety

| ID | Requirement |
|---|---|
| SEC-01 | All non-authentication endpoints require a valid session token. |
| SEC-02 | Secrets, tokens, and passwords are never written to logs or returned in API responses. |
| SEC-03 | Uploaded knowledge content never enters the Git repository. |
| SEC-04 | Uploaded filenames are sanitized; path traversal attempts are rejected. |
| SEC-05 | Model prompts must not be logged in full when they contain confidential document text. |
| SEC-06 | Deleting a document removes it from retrieval results immediately. |
| SEC-07 | Answers are treated as assistive output; the product must not present model output as an approved company record (see lesson L-006). |

---

## 9. Acceptance Criteria

v0.1 is accepted when a live demo on the pilot host satisfies all of the following.

| ID | Acceptance criterion |
|---|---|
| AC-01 | Three accounts exist (Admin, Editor, Viewer) and each role's capability matrix in section 2.2 is observably enforced. |
| AC-02 | A Viewer attempting to upload or delete is denied by the API, not only hidden in the UI. |
| AC-03 | Ten representative department documents are uploaded and all reach `indexed`, or any failure shows an actionable reason. |
| AC-04 | For ten representative business questions, at least eight answers carry citations that a reviewer confirms as relevant and traceable to the correct document. |
| AC-05 | At least one question with no supporting content returns an explicit "no basis" answer rather than an invented one. |
| AC-06 | A deleted document's content no longer appears in new answers or citations. |
| AC-07 | Reindex recovers a document that previously failed due to a transient error. |
| AC-08 | Session history persists across logout, login, and application restart. |
| AC-09 | Audit list shows entries for upload, delete, reindex, and role change performed during the demo. |
| AC-10 | The system is deployed and started from the documented Compose flow on a single host. |

---

## 10. Pilot Success Metrics

Adoption signals to review after the pilot period. These are not acceptance gates.

| Metric | Intent |
|---|---|
| Weekly active askers | Whether people return without being reminded |
| Questions per week | Whether it becomes a habit |
| Share of answers where the user opened a citation | Whether citations are trusted and used |
| Documents indexed | Whether maintainers keep feeding it |
| Reported wrong answers | Quality signal for retrieval tuning |

---

## 11. Open Questions

| ID | Question | Impact if unresolved |
|---|---|---|
| OQ-01 | Which model endpoint will the pilot use: an existing internal gateway, or a public API allowed by policy? | Blocks LLM adapter configuration and latency assumptions |
| OQ-02 | Are scanned or image-based PDFs in scope for the pilot corpus (would require OCR)? | Changes parsing selection and NFR-04 |
| OQ-03 | Which team is the first pilot group and what corpus do they contribute? | Blocks AC-03 and AC-04 test material |
| OQ-04 | Is there a designated company UI component library for intranet apps? | Frontend standards require an ADR before adopting a new kit |
| OQ-05 | Which retention rule applies to session history and audit entries? | Affects data model and later compliance requests |
| OQ-06 | Is embedding department documents into a third-party model endpoint acceptable under current policy? | May force a local embedding model |

OQ-01, OQ-02, and OQ-06 should be answered before the ingestion and ask slices are designed.

---

## 12. Proposed Slice Decomposition

Downstream slices derived from this specification. Each slice gets its own full SDD chain.

| Order | Slice key | Covers | Primary requirements |
|---|---|---|---|
| 1 | `repo-bootstrap` | Frontend shell, backend health endpoint, database and migration skeleton, Compose, env template | Enables all others |
| 2 | `auth-password-jwt` | Login, session token, roles, account administration | FR-01 to FR-07, FR-50 to FR-51 |
| 3 | `knowledge-ingest` | Upload, parse, chunk, embed, status, reindex, delete | FR-10 to FR-20 |
| 4 | `ask-rag` | Hybrid retrieval, cited answering, sessions, no-basis behavior | FR-30 to FR-40 |
| 5 | `audit-minimal` | Audit entries and Admin list view | FR-52 to FR-54 |

Suggested sequencing rationale: authentication before ingestion so uploads have an owner, and ingestion before answering so retrieval has content.

---

## 13. Roadmap After v0.1

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

## 14. Traceability Notes

- Downstream slice requirements must reference the FR / NFR / SEC / AC identifiers used here.
- Changes to scope in section 3 require updating this document before the affected slice is implemented.
- Product boundary claims must stay consistent with `docs/00-context/product-positioning.md` and ADR-0002.
