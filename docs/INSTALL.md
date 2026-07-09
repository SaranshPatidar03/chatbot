# Installation Guide

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker Desktop | Recommended |
| Ollama | Optional (local LLM) |

## 1. Clone and configure

```bash
git clone <your-repo-url> chatbot
cd chatbot
cp .env.example .env
```

Edit `.env`:

- `SECRET_KEY` or `JWT_SECRET` — random 32+ character string
- `DATABASE_URL`, `REDIS_URL` — match your environment
- `OPENAI_API_KEY` or `OLLAMA_BASE_URL` — at least one LLM provider
- `INITIAL_ADMIN_EMAIL` — first signup with this email becomes platform admin

## 2. Docker (recommended)

**Development:**

```bash
make up
```

- UI: http://localhost:5173
- API: http://localhost:8000/docs
- Mailpit: http://localhost:8025

**Production-like:**

```bash
make up-prod
```

- UI: http://localhost

## 3. Local development (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Worker (separate terminal):**

```bash
cd backend
arq app.workers.settings.WorkerSettings
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## 4. Verify installation

```bash
make test
make smoke
```

## 5. First login

1. Open the UI and sign up.
2. If using Mailpit, check http://localhost:8025 for verification/reset emails.
3. Upload documents in **Knowledge**, then chat in **Chat**.

See also: [DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY.md](SECURITY.md).
