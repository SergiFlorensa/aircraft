# Repository Guidelines

## Project Structure & Module Organization
- `backend/src/app` hosts the FastAPI service; API routers live under `api/`, shared config in `core/`, and DB utilities in `db/`.
- Domain models (e.g., `FlightEvent`) sit in `db/models.py`; expand here when introducing telemetry or alert aggregates.
- Tests live in `backend/tests` and should mirror the module layout (e.g., `test_health.py` exercises `api/routes_health.py`).
- Top-level `docker-compose.yml` orchestrates `backend`, `postgres`, and `redis`; docs and product intent stay in `docs/`.

## Build, Test, and Development Commands
- `cd backend; pip install -e .` installs the backend in editable mode using `pyproject.toml`.
- `cd backend; uvicorn app.main:app --reload` runs the API locally on port 8000.
- `docker compose up --build` spins up Postgres, Redis, and the API exactly as CI will.
- `cd backend; pytest` executes the current automated suite (see `test_health.py`).
- `cd backend; ruff check .` and `black .` keep the tree linted and formatted.

## Coding Style & Naming Conventions
- Target Python 3.11+, four-space indentation, 100-char lines (matching Ruff/Black config).
- Modules, packages, and functions use `snake_case`; classes stay in `PascalCase`; env vars remain `UPPER_SNAKE_CASE`.
- Prefer FastAPI routers per feature (e.g., `routes_events.py`) and keep Pydantic models near their endpoints for clarity.

## Testing Guidelines
- Pytest is the standard; new features need unit tests plus API tests via `fastapi.testclient` or `httpx.AsyncClient`.
- Name tests `test_<behavior>` and colocate fixtures in `conftest.py` when they are reused.
- When touching telemetry ingestion, verify DB state using SQLAlchemy sessions from `app.db.session.get_db`.

## Commit & Pull Request Guidelines
- No formal history exists yet, so follow Conventional Commits (e.g., `feat: add flight events router`) to keep the log searchable.
- Every PR should explain the change, list test evidence (`pytest`/`docker compose up` logs), and link any relevant issue.
- Include screenshots or API responses when UI or contract changes affect clients, and ensure docs or examples in `docs/` stay accurate.

## Security & Configuration Tips
- Store local secrets only in `.env`; never commit overrides with credentials.
- Update `app/core/config.py` when adding settings so that `Settings` exposes a single truth for env usage.
- Use Redis Streams for event ingestion; validate stream names and consumer groups in env vars to keep deployments deterministic.