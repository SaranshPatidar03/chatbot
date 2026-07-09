# Roadmap

Items below extend the current production-ready baseline without breaking existing APIs.

## Near term

- [ ] S3/MinIO object storage for multi-replica deployments
- [ ] Cross-encoder reranking and BM25 keyword index
- [ ] Redis embedding cache for repeated queries
- [ ] Authenticated Playwright E2E (upload → chat flow)
- [ ] Per-user analytics dashboard (`/analytics` user scope)
- [ ] Bulk platform reindex admin job

## Medium term

- [ ] Additional LLM providers (Anthropic, Gemini, Groq, OpenRouter)
- [ ] Agent tool calling (calculator, web search, safe code execution)
- [ ] Markdown rendering with syntax highlighting in chat
- [ ] Folder upload and drag-drop batch ingestion UI polish
- [ ] Let's Encrypt automation in Docker Compose

## Long term

- [ ] Voice (STT/TTS) conversation mode
- [ ] Image understanding and visual Q&A
- [ ] Multi-region HA with read replicas
- [ ] SSO (OIDC/SAML) enterprise login

## Completed (baseline)

- Grounded RAG with hybrid search, MMR, citations, streaming
- Auth (JWT, refresh rotation, sessions, password reset, email verification)
- Organizations, admin panel, user settings
- CI/CD, TLS overlay, Prometheus metrics
- Document ingestion (PDF, Office, OCR, ZIP, URLs)
