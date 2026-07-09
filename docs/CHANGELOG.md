# Changelog

## [Unreleased] — Enterprise hardening

### Added

- Email verification flow (`POST /auth/verify-email`, `POST /auth/resend-verification`)
- Session management API (`GET /auth/sessions`, `DELETE /auth/sessions/{id}`, `POST /auth/logout-all`)
- Chat export/import (`GET /chats/{id}/export`, `POST /chats/import`)
- Chat search API (`GET /chats/search`)
- Document reindex (`POST /documents/{id}/reindex`)
- Redis rate limiting middleware with `X-RateLimit-*` headers
- Production config validation for `SECRET_KEY` and `APP_DEBUG`
- `JWT_SECRET` alias for `SECRET_KEY`
- Frontend: chat pin/archive/delete/export/import, verify-email page
- Docs: `INSTALL.md`, `SECURITY.md`, `ROADMAP.md`, `CHANGELOG.md`, `CONTRIBUTING.md`
- Security headers middleware + nginx hardening headers
- BM25 keyword scoring in hybrid retrieval
- Redis query embedding cache
- Optional metrics scrape authentication
- Chat UI: markdown rendering, copy, rename, mobile sidebar, stop streaming
- `docs/AUDIT_REPORT.md`

### Improved

- `.gitignore` covers backend storage, logs, IDE caches
- `.env.example` documents all secret placeholders
- Access tokens rejected when server session is revoked/expired
- Stricter rate limits on `/auth/*` routes (`AUTH_RATE_LIMIT_REQUESTS`)
- N+1 org membership lookup removed from knowledge retrieval
- OpenAPI disabled in production unless `ENABLE_API_DOCS=true`

### Database

- Migration `20260709_email_verification` — `email_verification_tokens` table
- Migration `20260709_perf_indexes` — chat/message query indexes

## [0.1.0] — Phase 1–14

Initial production-ready grounded RAG chatbot with organizations, admin, Docker, and CI.
