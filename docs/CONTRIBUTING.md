# Contributing

## Development setup

See [INSTALL.md](INSTALL.md).

## Workflow

1. Create a feature branch from `main`.
2. Make focused changes; preserve backward compatibility.
3. Run tests: `make test`
4. Open a pull request with a clear description and test plan.

## Code standards

- **Python:** Follow existing FastAPI/SQLAlchemy patterns; use type hints.
- **TypeScript:** Match existing React Query + component structure.
- **Tests:** Add integration tests for new API routes in `tests/backend/`.
- **Docs:** Update `docs/API.md` for API changes.

## Commit messages

Use imperative mood: `Add session revocation API`, `Fix rate limit headers`.

## Do not commit

- `.env`, secrets, `node_modules`, `.venv`, uploads, or generated `dist/`
