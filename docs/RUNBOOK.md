# Operations Runbook

Day-2 operations for Knowledge Chatbot: monitoring, backups, restores, upgrades, and incident response.

Deployment prerequisites: [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 1. Health endpoints

| Endpoint | Purpose | Healthy | Unhealthy |
|----------|---------|---------|-----------|
| `GET /api/v1/health` | Liveness | `200`, `"status":"ok"` | Process down |
| `GET /api/v1/ready` | Readiness | `200`, `"status":"ready"` | `503`, dependency failure |
| `GET /api/v1/admin/system/health` | Admin detail | Requires `platform_admin` | — |

### Readiness checks

The `/ready` response includes per-dependency status:

- `postgres` — `SELECT 1`
- `redis` — `PING`
- `chromadb` — heartbeat

**Alert** when `/ready` returns 503 for more than 2 consecutive minutes.

### Quick checks

```bash
# Dev (API direct)
make health
make ready

# Prod (via nginx)
make smoke-prod
```

---

## 2. Logs

### Docker Compose

```bash
make logs                          # all dev services
docker compose logs -f backend     # API only
docker compose logs -f worker      # background jobs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx
```

### What to look for

| Log pattern | Meaning |
|-------------|---------|
| `request_completed` + `status_code=5xx` | API errors — check stack trace |
| `user_signup` / `user_login` | Auth activity |
| `document_ingest` / indexing errors | Worker or Chroma issues |
| `postgres_health_failed` | DB connectivity |
| `chromadb_health_failed` | Vector store down |

Structured fields include `request_id` — correlate across API and worker logs.

---

## 3. Backup procedures

### 3.1 PostgreSQL

**Docker (dev stack):**

```bash
docker compose exec -T postgres pg_dump -U chatbot -d chatbot -Fc > backup/chatbot_$(date +%Y%m%d_%H%M).dump
```

**Bare metal:**

```bash
pg_dump -h localhost -U chatbot -d chatbot -Fc > backup/chatbot_$(date +%Y%m%d_%H%M).dump
```

Schedule: daily minimum; retain 7–30 days per policy.

### 3.2 ChromaDB data

Chroma persists to the `chroma_data` Docker volume (or `CHROMA_PERSIST_DIR`).

```bash
# Find volume path
docker volume inspect knowledge-chatbot_chroma_data

# Stop writes briefly (optional, for consistent snapshot)
docker compose stop worker backend
docker run --rm -v knowledge-chatbot_chroma_data:/data -v $(pwd)/backup:/backup alpine \
  tar czf /backup/chroma_$(date +%Y%m%d).tar.gz -C /data .
docker compose start backend worker
```

### 3.3 Uploaded files

```bash
tar czf backup/storage_$(date +%Y%m%d).tar.gz -C storage uploads
```

Include `storage/uploads/` in the same backup schedule as Postgres.

---

## 4. Restore procedures

### 4.1 PostgreSQL

```bash
# Stop API/worker to prevent writes
docker compose stop backend worker

docker compose exec -T postgres pg_restore -U chatbot -d chatbot --clean --if-exists < backup/chatbot_YYYYMMDD.dump

docker compose start backend worker
```

Verify: `make ready` and spot-check user/document counts in admin panel.

### 4.2 Chroma

```bash
docker compose stop worker backend chromadb
# Restore volume contents from tar.gz into chroma_data volume
docker compose start chromadb backend worker
```

After Chroma restore, verify search and chat return expected citations. If vectors are missing but Postgres chunks exist, re-trigger indexing (re-upload or future reindex job).

### 4.3 Storage files

```bash
tar xzf backup/storage_YYYYMMDD.tar.gz -C storage
```

Ensure file paths in Postgres `documents` table still match files on disk.

---

## 5. Upgrade procedure

1. **Announce** maintenance window if migrations are expected
2. **Backup** Postgres + Chroma + storage (Section 3)
3. **Pull** new code / rebuild images:
   ```bash
   git pull
   make up-prod
   ```
4. **Migrations** run automatically on backend start; confirm in logs:
   ```
   Running database migrations...
   ```
   Or manually: `make migrate-docker`
5. **Verify**:
   ```bash
   make smoke-prod
   make test
   ```
6. **Functional smoke**: login → upload PDF → search → chat with citations

### Rollback

1. Deploy previous image tag / git revision
2. If migration was applied, restore Postgres from pre-upgrade dump (Alembic downgrade only if a down revision exists)

---

## 6. Scaling workers

Heavy document ingestion queues jobs in Redis (ARQ).

```bash
# Docker — add worker replicas
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale worker=3
```

Monitor Redis memory and worker logs for job failures. Each worker needs access to Postgres, Chroma, Redis, and the shared `storage/` volume.

---

## 7. Troubleshooting

### API returns 503 on `/ready`

| Failed check | Action |
|--------------|--------|
| `postgres` | Check container/service, credentials in `DATABASE_URL`, disk space |
| `redis` | Check Redis container, `REDIS_URL` |
| `chromadb` | Check Chroma container, network `CHROMA_HOST:CHROMA_PORT` |

### Documents stuck in `processing`

1. Check worker logs: `docker compose logs worker`
2. Confirm Redis is reachable
3. Confirm embedding provider works (Ollama model pulled or OpenAI key valid)
4. Check document `error_message` via API or admin documents list

### Chat returns refusal for known content

1. Confirm document `status` is `ready`
2. Run search in UI with same query — are results above threshold?
3. Check `RAG_SIMILARITY_THRESHOLD` and user settings
4. Verify Chroma collection has vectors (ingestion completed)

### SSE chat stream hangs

1. Check nginx `proxy_read_timeout` (300s in `docker/nginx.conf`)
2. Confirm `proxy_buffering off` on `/api/`
3. Test API directly (bypass nginx): `POST /api/v1/chats/{id}/messages`

### OpenAI / Ollama errors

| Provider | Check |
|----------|-------|
| OpenAI | `OPENAI_API_KEY`, quota, model name |
| Ollama | `ollama list`, model pulled, URL reachable from backend container |

```bash
# From backend container
docker compose exec backend curl -fsS http://host.docker.internal:11434/api/tags
```

### Password reset emails not sent

1. Verify `SMTP_*` settings (not Mailpit in production)
2. Check backend logs for SMTP errors
3. Confirm `FRONTEND_URL` is correct in reset links

### Admin panel 403

- User must have `role: platform_admin`
- Bootstrap via `INITIAL_ADMIN_EMAIL` on first signup, or promote via existing admin

---

## 8. Incident response

### Severity guide

| Level | Example | Response |
|-------|---------|----------|
| P1 | API down, data loss risk | Restore from backup, all hands |
| P2 | Readiness failing, chat broken | Fix dependency, communicate ETA |
| P3 | Slow ingestion, single user issue | Worker scale, support ticket |

### P1 — Full outage

1. Confirm scope: `curl /api/v1/health` and `/ready`
2. Check `docker compose ps` — restart crashed containers
3. If data corruption suspected → stop writes, restore from latest backup
4. Post-incident: document root cause, update runbook

### P2 — Degraded (readiness 503)

1. Identify failing dependency from `/ready` JSON `checks`
2. Restart affected service
3. If Postgres disk full → expand volume, vacuum

### P2 — LLM provider outage

- Users can still search/browse documents
- Chat returns errors or refusals — switch `DEFAULT_LLM_PROVIDER` if alternate is configured, restart backend

---

## 9. Maintenance tasks

| Task | Frequency |
|------|-----------|
| Postgres backup | Daily |
| Chroma + storage backup | Daily or weekly |
| Test restore | Monthly |
| Review audit logs (admin) | Weekly |
| Rotate secrets (SMTP, API keys) | Per policy |
| `docker system prune` (dev machines) | As needed |
| Dependency security updates | Monthly |

---

## 10. Support commands reference

```bash
make up              # Dev stack
make up-prod         # Production-like stack
make down            # Stop stacks
make migrate-docker  # Run Alembic in backend container
make docker-config   # Validate compose files
make test            # Backend + frontend tests
make smoke-prod      # Health via nginx :80
```
