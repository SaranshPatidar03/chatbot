# Deployment Guide

This guide covers production deployment for Knowledge Chatbot: prerequisites, environment configuration, Docker and bare-metal paths, TLS, first admin bootstrap, and post-deploy verification.

For day-2 operations (backup, restore, upgrades, incidents), see [RUNBOOK.md](RUNBOOK.md).

---

## 1. Architecture summary

| Component | Role | Production recommendation |
|-----------|------|---------------------------|
| **Frontend** | React SPA | Static build behind Nginx or CDN |
| **Backend** | FastAPI API | 2+ stateless replicas behind load balancer |
| **Worker** | ARQ background jobs | 1+ replicas (ingest, embed, reindex) |
| **PostgreSQL** | Relational data | Managed Postgres 16+ |
| **Redis** | Cache, rate limits, ARQ queue | Managed Redis 7+ |
| **ChromaDB** | Vector index | Persistent volume or dedicated host |
| **Object storage** | Uploaded files | Local `storage/` volume or S3-compatible (future) |
| **LLM** | OpenAI and/or Ollama | API key or self-hosted Ollama |
| **SMTP** | Password reset email | Transactional email provider |

Traffic flow (production compose):

```
Browser → Nginx (:80) → /api/* → Backend (:8000)
                      → /*     → Frontend static (:80)
```

---

## 2. Prerequisites

### Minimum (single-node / small team)

- 4 CPU cores, 8 GB RAM (16 GB if running Ollama on the same host)
- 50 GB SSD (more if storing large document libraries)
- Docker Engine 24+ and Docker Compose v2
- Outbound HTTPS for OpenAI (if used)

### Recommended (production)

- Separate hosts or managed services for Postgres, Redis, and Chroma
- TLS certificate (Let's Encrypt or load balancer termination)
- Secret manager or encrypted `.env` injection (not committed to git)
- Automated backups with tested restore procedure

### Software (bare-metal path)

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+, Redis 7+, ChromaDB 0.5+
- Tesseract OCR, Poppler (see `docker/backend.Dockerfile` packages)
- Nginx or equivalent reverse proxy

---

## 3. Pre-deployment checklist

Copy and complete before going live:

- [ ] Generate a strong `SECRET_KEY` (64+ random bytes, base64 or hex)
- [ ] Set unique `POSTGRES_PASSWORD` (not the example default)
- [ ] Set `APP_ENV=production` and `APP_DEBUG=false`
- [ ] Set `CORS_ORIGINS` and `FRONTEND_URL` to your real public origin(s)
- [ ] Configure `SMTP_*` for password-reset email (not Mailpit)
- [ ] Set `INITIAL_ADMIN_EMAIL` to your bootstrap admin address
- [ ] Configure LLM provider (`OPENAI_API_KEY` and/or `OLLAMA_BASE_URL`)
- [ ] Confirm `RAG_ALLOW_GENERAL_KNOWLEDGE=false` (grounded-only answers)
- [ ] Ensure Postgres, Redis, and Chroma are **not** exposed on public ports
- [ ] Plan backups for Postgres, Chroma volume, and `storage/uploads/`
- [ ] Document who receives alerts when `/ready` returns 503

---

## 4. Environment configuration

Copy the template and edit:

```bash
cp .env.example .env
```

### Critical production variables

| Variable | Purpose | Production example |
|----------|---------|-------------------|
| `SECRET_KEY` | JWT signing | Long random string |
| `APP_ENV` | Environment label | `production` |
| `APP_DEBUG` | Verbose errors | `false` |
| `FRONTEND_URL` | Links in emails | `https://chat.example.com` |
| `CORS_ORIGINS` | Allowed browser origins | `https://chat.example.com` |
| `DATABASE_URL` | Async SQLAlchemy URL | `postgresql+asyncpg://user:pass@db:5432/chatbot` |
| `REDIS_URL` | Cache / rate limit | `redis://redis:6379/0` |
| `ARQ_REDIS_URL` | Worker queue | Same or dedicated Redis DB index |
| `CHROMA_HOST` / `CHROMA_PORT` | Vector store | Internal hostname, `8000` in Docker network |
| `DEFAULT_LLM_PROVIDER` | `openai` or `ollama` | Match your infra |
| `OPENAI_API_KEY` | OpenAI access | Set if using OpenAI |
| `OLLAMA_BASE_URL` | Ollama HTTP API | `http://ollama:11434` or host URL |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_TLS` | Outbound email | Provider-specific |
| `INITIAL_ADMIN_EMAIL` | First platform admin | `admin@yourcompany.com` |

### Docker-specific overrides

| Variable | Dev default | Prod compose |
|----------|-------------|--------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | `/api/v1` (relative, baked at build) |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Reachable Ollama URL from containers |
| `NGINX_PORT` | — | `80` (or `443` with external TLS proxy) |

Full list: [`.env.example`](../.env.example) and `backend/app/core/config.py`.

---

## 5. Deploy with Docker Compose (recommended)

### 5.1 Production-like stack (single host)

```bash
cp .env.example .env
# Edit .env — see checklist above

make up-prod
# equivalent:
# docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

What this starts:

| Service | Exposed | Notes |
|---------|---------|-------|
| `nginx` | `:80` | Single entrypoint |
| `backend` | internal | Auto-runs Alembic on start |
| `worker` | internal | ARQ ingest/embed jobs |
| `frontend` | internal | Static nginx image |
| `postgres`, `redis`, `chromadb` | internal only | Not published in prod overlay |

Migrations run automatically via `docker/backend.entrypoint.sh` before uvicorn starts.

### 5.2 Development stack

```bash
make up
# docker compose --profile dev up -d --build
```

Hot reload, Vite on `:5173`, API on `:8000`, Mailpit on `:8025`.

### 5.3 Post-deploy verification

```bash
make smoke-prod
```

Or manually:

```bash
curl -fsS http://localhost/api/v1/health
curl -fsS http://localhost/ready
```

Expected: health `status: ok`, readiness `status: ready` when Postgres, Redis, and Chroma are up.

### 5.4 First admin user

1. Set `INITIAL_ADMIN_EMAIL=you@company.com` in `.env`
2. Restart backend if already running: `docker compose restart backend`
3. Open the app → **Sign up** with that exact email
4. The account receives `platform_admin` and can access `/app/admin`

### 5.5 Ollama (optional, self-hosted LLM)

On the Docker host:

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

Containers use `OLLAMA_BASE_URL=http://host.docker.internal:11434` by default in dev compose. In production, run Ollama on a reachable host and point `OLLAMA_BASE_URL` there.

---

## 6. Bare-metal / VM deployment

Use this when not using the bundled Compose stack (e.g. managed Postgres on RDS).

### 6.1 Database

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

### 6.2 API process

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Use systemd, supervisord, or your orchestrator to keep this running.

### 6.3 Worker process

```bash
cd backend
arq app.workers.settings.WorkerSettings
```

Run at least one worker replica. Scale horizontally for heavy ingestion load.

### 6.4 Frontend build

```bash
cd frontend
npm ci
VITE_API_BASE_URL=/api/v1 npm run build
```

Serve `frontend/dist/` with Nginx (`try_files` → `index.html` for SPA routing). See `docker/frontend.nginx.conf`.

### 6.5 Reverse proxy

Proxy `/api/`, `/docs`, `/openapi.json`, `/health`, `/ready`, `/metrics` to the backend. Proxy `/` to static frontend. For SSE chat streaming:

- `proxy_buffering off`
- `proxy_read_timeout 300s`

Reference: `docker/nginx.conf`.

---

## 7. TLS / HTTPS

The default production compose serves HTTP on port 80. For production you can:

1. **Terminate TLS at a cloud load balancer** (ALB, Cloudflare, etc.) → forward HTTP to nginx, or
2. **Use the bundled TLS overlay** (self-signed or mounted real certs), or
3. **Add Certbot** on the host, or use **Traefik/Caddy** with automatic certificates

### 7.1 Bundled TLS overlay (single host)

Generate development certificates (requires OpenSSL):

```bash
make tls-certs
make up-prod-tls
```

This starts the prod stack with `docker-compose.tls.yml`, redirects HTTP → HTTPS, and listens on `:443`.

Mount real certificates by replacing files in `docker/certs/`:

- `fullchain.pem`
- `privkey.pem`

Then set in `.env`:

```bash
FRONTEND_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com
```

### 7.2 External TLS termination

When TLS terminates upstream, set:

- `FRONTEND_URL=https://your-domain.com`
- `CORS_ORIGINS=https://your-domain.com`

Ensure the proxy sets `X-Forwarded-Proto: https` so redirects and cookies behave correctly.

---

## 8. Scaling

| Layer | How to scale |
|-------|----------------|
| API | Increase uvicorn `--workers` or run multiple backend containers behind a load balancer |
| Workers | `docker compose up -d --scale worker=3` or multiple `arq` processes |
| Postgres | Vertical scale or read replicas (app uses primary for writes) |
| Redis | Single instance is usually sufficient; use Redis Cluster for very high throughput |
| Chroma | Single instance with persistent volume; shard by collection for multi-tenant scale-out |

All API replicas must share: same Postgres, Redis, Chroma, and `storage/` volume (or shared object storage).

---

## 9. Security hardening

- Never commit `.env` or API keys
- Rotate `SECRET_KEY` only with a planned session invalidation (all users re-login)
- Restrict admin routes to VPN or IP allowlist at the proxy if possible
- Keep `RAG_ALLOW_GENERAL_KNOWLEDGE=false` unless product policy explicitly allows general knowledge
- Run `make test` in CI before each release
- Review audit logs via `/app/admin` after go-live

---

## 10. Release checklist

1. `git pull` / deploy new image tag
2. `make test` (or CI green)
3. Backup Postgres (see [RUNBOOK.md](RUNBOOK.md))
4. Deploy: `make up-prod` (rebuild) or rolling update of API/worker
5. Migrations: automatic on backend start, or `make migrate-docker`
6. `make smoke-prod`
7. Smoke test: signup/login, upload document, search, chat stream, admin panel
8. Monitor logs for 15 minutes

---

## 11. Related documentation

| Document | Contents |
|----------|----------|
| [RUNBOOK.md](RUNBOOK.md) | Backup, restore, upgrades, troubleshooting |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, tenancy, RAG pipeline |
| [API.md](API.md) | REST endpoints and SSE chat protocol |
| [README.md](../README.md) | Quick start and project overview |
