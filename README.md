# Knowledge Chatbot

Production-oriented AI chatbot that answers **only** from your uploaded knowledge base.
If the answer is not in retrieved context, it responds:

> I could not find this information in the provided knowledge base.

## Features (phased delivery)

- Hybrid tenancy: personal KBs + shared organizations
- Document ingestion (PDF, Office, text, CSV, Markdown, HTML, ZIP, URLs, OCR)
- Advanced RAG: hybrid search, MMR, parent-child chunks, citations, streaming chat
- Dual LLM providers: OpenAI + Ollama
- Auth (JWT), admin, settings, Docker stack

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full design.

## Tech stack

| Layer | Stack |
|-------|--------|
| Frontend | React, TypeScript, Vite, Tailwind, ShadCN, Framer Motion, React Query, Axios |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, ARQ |
| Data | PostgreSQL, ChromaDB, Redis |
| LLM | OpenAI API, Ollama |

## Project structure

```
chatbot/
  backend/          FastAPI application
  frontend/         React + Vite SPA (includes `frontend/tests/` Vitest suite)
  docker/           Dockerfiles & nginx
  docs/             Architecture & deployment docs
  tests/backend/    Pytest suite
  frontend/e2e/     Playwright E2E smoke tests
  .github/workflows/  CI (backend, frontend, E2E, compose validate)
  storage/          Local uploads (gitignored)
```

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (recommended for full stack)
- Optional: [Ollama](https://ollama.com) for local models

### 1. Configure environment

```bash
cp .env.example .env
# Edit SECRET_KEY and provider keys as needed
```

### 2. Run with Docker Compose

**Development (hot reload, Vite on :5173, API on :8000):**

```bash
make up
# or: docker compose --profile dev up -d --build
```

**Production-like stack (nginx on :80, static frontend, API workers):**

```bash
make up-prod
# or: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Services:

| Service | Dev URL | Prod URL (via nginx) |
|---------|---------|----------------------|
| Frontend | http://localhost:5173 | http://localhost |
| Backend API | http://localhost:8000 | http://localhost/api/v1 |
| OpenAPI docs | http://localhost:8000/docs | http://localhost/docs |
| Mailpit UI (`--profile dev`) | http://localhost:8025 | — |
| ChromaDB | http://localhost:8001 | internal only |

### 3. Local development (without full compose)

**Backend**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## Configuration

All settings are documented in [`.env.example`](.env.example). Key variables:

- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` / `ARQ_REDIS_URL` — cache & workers
- `OPENAI_API_KEY` / `OLLAMA_BASE_URL` — LLM providers
- `DEFAULT_LLM_PROVIDER` — `openai` or `ollama`
- `RAG_ALLOW_GENERAL_KNOWLEDGE` — must stay `false` for grounded-only answers

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API overview](docs/API.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Operations runbook](docs/RUNBOOK.md)

## Development phases

Phases 1–13 delivered core product features. Phase 14 adds production polish.

| Phase | Scope |
|-------|--------|
| 1 | Project architecture |
| 2 | Backend foundation |
| 3 | Frontend foundation |
| 4 | Authentication |
| 5 | Knowledge ingestion |
| 6 | Embeddings |
| 7 | RAG pipeline |
| 8 | Chat interface |
| 9 | Admin panel |
| 10 | Testing |
| 11 | Docker polish |
| 12 | Deployment docs & runbooks |
| 13 | Organizations (hybrid tenancy UI + API) |
| 14 | User settings API, dashboard summary, CI/CD, TLS overlay, E2E, Prometheus metrics |

### Frontend routes (Phase 3)

| Route | Description |
|-------|-------------|
| `/` | Public landing |
| `/login`, `/signup` | Auth pages |
| `/forgot-password`, `/reset-password` | Password recovery |
| `/app` | Dashboard (protected) |
| `/app/chat` | Chat shell |
| `/app/knowledge` | Knowledge base shell |
| `/app/search` | Search shell |
| `/app/settings` | Settings |
| `/app/admin` | Admin (platform_admin only) |

Keyboard shortcuts: `Alt+D` dashboard, `Alt+C` chat, `Alt+K` knowledge, `Alt+S` search, `Alt+,` settings.

## License

Proprietary — all rights reserved unless otherwise stated.
