# Security Policy

## Reporting vulnerabilities

Report security issues privately to your platform administrator. Do not open public issues for undisclosed vulnerabilities.

## Secrets management

- Never commit `.env`, API keys, or TLS private keys.
- Use `SECRET_KEY` or `JWT_SECRET` (32+ random bytes) in production.
- Rotate `SECRET_KEY` only with a planned session invalidation (all users re-login).
- Store production secrets in a secret manager or encrypted injection pipeline.

## Authentication

- Passwords hashed with **bcrypt**.
- Access tokens are short-lived JWTs; refresh tokens rotate on each `/auth/refresh`.
- Sessions stored server-side with revocation support.
- Optional `REQUIRE_EMAIL_VERIFICATION=true` blocks login until email is verified.
- Password reset invalidates all active sessions.

## Transport

- Use HTTPS in production (`make up-prod-tls` or terminate TLS at a load balancer).
- Set `FRONTEND_URL` and `CORS_ORIGINS` to your real HTTPS origin.

## API protection

- Redis-backed rate limiting (`RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS`).
- Stricter limits on authentication routes (`AUTH_RATE_LIMIT_REQUESTS`, default 20/min).
- HTTP security headers from the API (`SecurityHeadersMiddleware`) and nginx in production.
- Prometheus metrics at `/metrics` — set `METRICS_REQUIRE_AUTH=true` and `METRICS_SCRAPE_TOKEN` in production.
- OpenAPI/Swagger disabled in production unless `ENABLE_API_DOCS=true`.
- Platform admin routes require `platform_admin` role.
- Access tokens include a session id (`sid`); revoked sessions invalidate the token immediately.

## Data isolation

- Personal knowledge bases are scoped per user (`kb_{user_id}`).
- Organization libraries require membership (`kb_org_{org_id}`).
- Grounded RAG: answers derived from retrieved context unless explicitly allowed by policy.

## Production checklist

1. `APP_ENV=production`, `APP_DEBUG=false`
2. Strong `SECRET_KEY` / `JWT_SECRET`
3. Unique database and Redis passwords
4. SMTP configured for password reset and verification emails
5. Postgres, Redis, Chroma not exposed on public ports
6. Automated backups with tested restore (see `docs/RUNBOOK.md`)
