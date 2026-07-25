# quarry-kb-draft (copy source)

Staging area for artifacts authored here and intended to be copied into the `quarry-kb` repository. Nothing in this folder belongs to this repository's product.

## Copy Targets

| File here | Destination in `quarry-kb` |
|---|---|
| `docs/01-requirements/quarry-kb-product-spec-v0.1.md` | `docs/01-requirements/quarry-kb-product-spec-v0.1.md` |
| `docs/prototypes/index.html` | `docs/prototypes/index.html` |
| `docs/prototypes/README.md` | `docs/prototypes/README.md` |

Paths are already aligned, so the folder can be copied as-is:

```sh
cp -R quarry-kb-draft/docs/. /path/to/quarry-kb/docs/
```

## Notes For The Destination Repo

- The product specification is a **requirements-layer input**, not a slice SDD set. Slice documents (`repo-bootstrap`, `auth-password-jwt`, `knowledge-ingest`, `ask-rag`, `audit-minimal`) should be generated from it via `wwa-sdd-generate-all`.
- Adding `docs/prototypes/` also resolves a previously dangling reference in the `wwa-sdd-generate-all` skill.
- Both files are English-only, matching the repository language rule.
- Content is mock-only: no real company documents, names, or systems.

## Platform Decisions Locked In Spec v0.1.5

| ID | Decision |
|---|---|
| D-01 | Chat via **configurable** OpenAI-compatible providers: internal gateway **and** public (e.g. DeepSeek). Ask-time snippets may leave intranet if public chat is selected. |
| D-02 | Scanned PDFs in scope; **OCR required** |
| D-03 | Document text **must not** go to any external **embedding** service |
| D-04 | Embeddings via **internal gateway embedding API** |
| D-05 | OCR via **internal gateway multimodal** |
| D-06 | **Multiple public** chat providers may be enabled; **any authenticated user** can switch provider on Ask |
| D-07 | Gateway down → **Browse full**; **Upload accept then fail ingest clearly**; **Ask** keyword-fallback / clear chat error (no silent provider switch) |

## Still Open

- `OQ-03` pilot group and corpus
- `OQ-04` UI component library
- `OQ-05` retention
- `OQ-09` exact gateway URLs / model ids / multimodal path
