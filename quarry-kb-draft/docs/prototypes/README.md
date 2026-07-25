# Prototypes

Static, mock-only prototypes for Quarry KB. These files illustrate intended product behavior. They are not an implementation and must never be wired to real services.

## Current Prototype

| File | Scope |
|---|---|
| `index.html` | v0.1 walkthrough: Login, Ask, Knowledge, Document detail, Admin/Users |

## How To Open

```sh
open docs/prototypes/index.html
```

No install step, build system, server, CDN, or framework is required.

## What The Prototype Demonstrates

- Role preview (`Admin` / `Editor` / `Viewer`) and how capability differences appear in the UI
- Ask screen with inline citation markers and an expandable sources panel
- Explicit "no basis found" answer state (requirement FR-35)
- Knowledge list with ingestion status pills (`Queued`, `Parsing`, `Indexed`, `Failed`)
- Document detail with chunk preview, ingestion timeline, and Editor-only actions
- Admin user list with role assignment and a minimal audit list
- Deliberately disabled `Wiki` navigation and `Agent` mode, labeled as later

## Deliberate Omissions

Streaming answers, multi-collection navigation, SSO login, tag management, upload progress detail, and pagination are not modeled in v0.1.

## Rules

- Mock content only. No real company documents, filenames, screenshots, people, or system names.
- Role behavior in the prototype is illustrative. Authorization is enforced server-side per `docs/standards/backend.md`.
- When product scope changes, update `docs/01-requirements/quarry-kb-product-spec-v0.1.md` first, then the prototype.
