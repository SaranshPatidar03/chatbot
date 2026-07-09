.PHONY: help install-backend install-frontend install up up-prod up-prod-tls down logs migrate migrate-docker docker-config tls-certs test test-backend test-frontend test-e2e health ready smoke smoke-prod

help:
	@echo "Knowledge Chatbot — common targets"
	@echo "  make install          Install backend + frontend deps"
	@echo "  make install-backend  Install Python deps"
	@echo "  make install-frontend Install Node deps"
	@echo "  make up               Start dev Docker stack (hot reload)"
	@echo "  make up-prod          Start production-like Docker stack (nginx :80)"
	@echo "  make up-prod-tls      Prod stack with HTTPS on :443 (run tls-certs first)"
	@echo "  make tls-certs        Generate self-signed certs in docker/certs/"
	@echo "  make down             Stop Docker Compose stack"
	@echo "  make logs             Tail Compose logs"
	@echo "  make migrate          Run Alembic migrations (local venv)"
	@echo "  make migrate-docker   Run Alembic migrations in backend container"
	@echo "  make docker-config    Validate Compose files"
	@echo "  make test             Run backend + frontend tests"
	@echo "  make test-backend     Run backend tests only"
	@echo "  make test-frontend    Run frontend tests only"
	@echo "  make test-e2e         Run Playwright E2E tests"
	@echo "  make health           Hit API health endpoint"
	@echo "  make ready            Hit API readiness endpoint"
	@echo "  make smoke            Health + readiness (dev API :8000)"
	@echo "  make smoke-prod       Health + readiness (prod nginx :80)"

install: install-backend install-frontend

install-backend:
	cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt || .venv/bin/pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

up:
	docker compose --profile dev up -d --build

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

up-prod-tls:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.tls.yml up -d --build

tls-certs:
	powershell -ExecutionPolicy Bypass -File scripts/gen-dev-certs.ps1 || bash scripts/gen-dev-certs.sh

down:
	docker compose --profile dev down
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
	docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.tls.yml down

logs:
	docker compose --profile dev logs -f

migrate:
	cd backend && alembic upgrade head

migrate-docker:
	docker compose exec backend alembic upgrade head

docker-config:
	docker compose --profile dev config
	docker compose -f docker-compose.yml -f docker-compose.prod.yml config
	docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.tls.yml config

test: test-backend test-frontend

test-backend:
	cd backend && set PYTHONPATH=.;../tests/backend&& .venv/Scripts/pytest ../tests/backend -q || (cd backend && PYTHONPATH=.:../tests/backend .venv/bin/pytest ../tests/backend -q)

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

health:
	curl -s http://localhost:8000/api/v1/health || curl -s http://localhost:8000/health

ready:
	curl -s http://localhost:8000/api/v1/ready || curl -s http://localhost:8000/ready

smoke: health ready

smoke-prod:
	curl -fsS http://localhost/api/v1/health
	curl -fsS http://localhost/ready
