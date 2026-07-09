# API Overview

Base URL (local): `http://localhost:8000/api/v1`  
Base URL (production compose via nginx): `http://localhost/api/v1`

Interactive OpenAPI: `/docs` on the same host as the API.

Deployment and operations: [DEPLOYMENT.md](DEPLOYMENT.md), [RUNBOOK.md](RUNBOOK.md).

## Conventions

- JSON request/response bodies (except multipart uploads and SSE streams)
- Bearer JWT on protected routes: `Authorization: Bearer <access_token>`
- Errors: `{ "detail": "...", "code": "optional_machine_code" }`
- Pagination: `?page=1&page_size=20` with `{ items, total, page, page_size }`

## Route groups (planned)

| Prefix | Purpose |
|--------|---------|
| `/health` | Liveness / readiness |
| `/auth` | Signup, login, refresh, logout, password reset, profile |
| `/documents` | Upload, list, delete, versions, preview |
| `/search` | Semantic, keyword, hybrid search |
| `/chats` | CRUD chats, messages, stream generation |
| `/settings` | User RAG/LLM preferences |
| `/admin` | Users, storage, logs, models, analytics |
| `/analytics` | Usage metrics (user + admin scoped) |
| `/organizations` | Org CRUD and membership |

## Health (Phase 2)

```
GET /api/v1/health
GET /health
GET /api/v1/ready
GET /ready
```

Liveness example:

```json
{
  "status": "ok",
  "app": "Knowledge Chatbot",
  "version": "0.1.0",
  "phase": 2,
  "environment": "development"
}
```

Readiness returns `200` when Postgres, Redis, and Chroma are reachable; otherwise `503` with per-dependency status in `checks`.

## Auth (Phase 4)

- `POST /auth/signup` — create account, returns tokens + user
- `POST /auth/login` — authenticate, returns tokens + user
- `POST /auth/refresh` — body: `{ "refresh_token": "..." }`
- `POST /auth/logout` — requires Bearer token; optional `{ "refresh_token": "..." }`
- `POST /auth/forgot-password` — always returns generic success message
- `POST /auth/reset-password` — body: `{ "token", "password" }`
- `GET /auth/me` — current user profile
- `PATCH /auth/me` — update `full_name`, `avatar_url`

## Documents (Phase 5)

All routes require Bearer authentication. Supported uploads: PDF, DOCX, TXT, CSV, JSON, HTML, PPTX, XLSX, images (OCR), and ZIP archives. Ingestion extracts text, chunks it, and stores metadata in Postgres (vector indexing lands in Phase 6).

- `POST /documents/upload` — multipart field `files` (one or more files); returns `201` with array of document objects
- `POST /documents/url` — body: `{ "url": "https://...", "title": "optional" }`
- `GET /documents` — paginated list (`page`, `page_size`)
- `GET /documents/{id}` — document metadata
- `GET /documents/{id}/content` — extracted plain text from stored chunks
- `DELETE /documents/{id}` — soft-delete document

Document status lifecycle: `pending` → `processing` → `ready` | `failed`. Phase 6 embeds each chunk and indexes vectors in ChromaDB (collection per user or org). Chunk rows store `chroma_id` and `embedding_model` after indexing.

Example document object:

```json
{
  "id": "uuid",
  "title": "notes.txt",
  "original_filename": "notes.txt",
  "content_type": "text/plain",
  "extension": "txt",
  "file_size_bytes": 128,
  "content_hash": "sha256...",
  "scope": "personal",
  "status": "ready",
  "version": 1,
  "page_count": null,
  "chunk_count": 3,
  "source_url": null,
  "error_message": null,
  "processed_at": "2026-07-08T12:00:00Z",
  "created_at": "2026-07-08T12:00:00Z",
  "updated_at": "2026-07-08T12:00:00Z",
  "meta": {}
}
```

## Search (Phase 7)

Requires Bearer authentication. Retrieves ranked chunks from the user's personal and organization Chroma collections using semantic, keyword, or hybrid fusion, then applies MMR re-ranking and similarity threshold filtering.

- `POST /search` — body:

```json
{
  "query": "leave policy",
  "mode": "hybrid",
  "top_k": 8,
  "filters": {
    "scope": "all",
    "document_ids": null,
    "organization_id": null
  }
}
```

Response:

```json
{
  "query": "leave policy",
  "mode": "hybrid",
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "title": "policy.txt",
      "content": "Our leave policy grants 20 days...",
      "page_number": null,
      "chunk_index": 0,
      "score": 0.82,
      "semantic_score": 0.75,
      "keyword_score": 1.0,
      "scope": "personal",
      "citation": "policy.txt (chunk 0)"
    }
  ],
  "total_candidates": 3,
  "has_sufficient_context": true
}
```

`has_sufficient_context` is `true` when at least one result meets the configured similarity threshold (user settings override app defaults).

## Chat (Phase 8)

Requires Bearer authentication. Messages use grounded RAG retrieval and stream via **Server-Sent Events (SSE)**.

- `GET /chats` — list chats (pinned first)
- `POST /chats` — create chat (`title`, optional `organization_id`)
- `PATCH /chats/{id}` — update `title`, `is_pinned`, `is_archived`
- `DELETE /chats/{id}` — delete chat and messages
- `GET /chats/{id}/messages` — list messages with citations
- `POST /chats/{id}/messages` — send user message; streams SSE events:
  - `start` — `{ user_message_id }`
  - `citations` — `{ citations: [...] }`
  - `token` — `{ content }` (repeat)
  - `done` — `{ message_id, latency_ms }`
- `POST /chats/{id}/messages/{message_id}/regenerate` — regenerate assistant reply (SSE)

Assistant messages persist `citations` JSON (chunk, document, page, score). Insufficient retrieval returns the grounded refusal message with empty citations.

Document viewer support:
- `GET /documents/{id}/content` — extracted text
- `GET /documents/{id}/file` — original uploaded file

## Admin (Phase 9)

Requires Bearer authentication and `platform_admin` role.

- `GET /admin/users` — paginated user list (`q`, `role`, `is_active`)
- `GET /admin/users/{id}` — user detail with document/chat counts
- `PATCH /admin/users/{id}` — update `role`, `is_active`, `is_verified`
- `GET /admin/documents` — platform-wide document list
- `GET /admin/storage/summary` — total bytes and counts by status
- `DELETE /admin/documents/{id}` — admin soft-delete (purges vectors)
- `GET /admin/audit-logs` — paginated audit trail
- `GET /admin/analytics/summary` — aggregated metrics (`days` query param)
- `GET /admin/analytics/events` — raw analytics events
- `GET /admin/system/health` — extended readiness probe
- `GET /admin/system/config` — read-only safe configuration snapshot

Bootstrap: set `INITIAL_ADMIN_EMAIL` so the first signup with that email receives `platform_admin`.

## Organizations (Phase 13)

Requires Bearer authentication. Roles: `owner`, `admin`, `member`.

- `GET /organizations` — organizations the current user belongs to
- `POST /organizations` — create workspace (creator becomes `owner`)
- `GET /organizations/{id}` — organization detail
- `PATCH /organizations/{id}` — update name/description (`owner` or `admin`)
- `DELETE /organizations/{id}` — delete workspace (`owner` only; purges vectors)
- `GET /organizations/{id}/members` — list members
- `POST /organizations/{id}/members` — add member by email (`owner` or `admin`)
- `PATCH /organizations/{id}/members/{user_id}` — update member role
- `DELETE /organizations/{id}/members/{user_id}` — remove member or leave org

Documents support `?organization_id=` on upload, URL ingest, and list for shared libraries.

## Settings (Phase 14)

Requires Bearer authentication. Preferences apply to chat generation, retrieval, and embedding during indexing.

- `GET /settings` — current user's LLM/RAG preferences
- `PATCH /settings` — partial update (providers, models, temperature, top-k, system prompt, etc.)

`allow_general_knowledge` can only be enabled when the platform sets `RAG_ALLOW_GENERAL_KNOWLEDGE=true`.

## Dashboard (Phase 14)

- `GET /dashboard/summary` — document/chat counts, storage bytes, processing queue size, recent activity

## Metrics (Phase 14)

- `GET /metrics` — Prometheus exposition format (`http_requests_total`, `http_request_duration_seconds`)

Scrape from the API host or via nginx in production (`/metrics` is proxied).

Detailed schemas are generated from Pydantic models as endpoints are implemented.
