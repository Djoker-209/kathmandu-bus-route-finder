# Backend — Kathmandu Bus Route Finder

FastAPI + NetworkX (graph engine) + PostGIS data access layer.

For the full project overview (frontend, tech stack, team), see the [root README](../README.md).

## Prerequisites

- Python 3.11
- Docker (for Postgres + PostGIS)

## Setup

```bash
# 1. Start Postgres + PostGIS (from the repo root, not backend/)
cd ..
docker compose up -d db
cd backend

# 2. Create your local env file
cp .env.example .env
# Defaults in .env.example match docker-compose.yml, so no edits needed
# for local dev. If you change DB credentials in docker-compose.yml,
# update .env to match.

# 3. Python environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Apply migrations (creates stops / routes / route_stops / etc.)
alembic upgrade head

# 5. Run the API
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000` (interactive docs at `/docs`).

## Running tests

```bash
pytest -v
```

Some tests in `tests/` (e.g. `test_stops.py`) require a live database and will skip cleanly if one isn't reachable — make sure `docker compose up -d db` has been run first and migrations are applied, or those tests will just no-op.

Pure-logic routing tests (no DB needed) live separately in `app/graph_engine/tests/`.

## Inspecting the live database

Useful for debugging model/schema mismatches:

```bash
docker exec -it ktm_bus_db psql -U ktm_bus -d ktm_bus_route_finder -c "\d <table_name>"
```

Or drop into an interactive session:

```bash
docker exec -it ktm_bus_db psql -U ktm_bus -d ktm_bus_route_finder
```

## Database migrations

Schema changes are tracked with Alembic (`migrations/`).

```bash
alembic upgrade head                     # apply all migrations
alembic revision -m "add fare column"    # create a new migration
alembic downgrade -1                     # roll back one step
```

**Important:** SQLAlchemy models in `app/models/` are hand-written and not auto-generated from migrations. After writing or applying a migration that changes a table, manually update the corresponding model file to match — column names, types, and nullability must match exactly, or you'll get failures that only show up at query time rather than at import time. Cross-check with:

```bash
docker exec -it ktm_bus_db psql -U ktm_bus -d ktm_bus_route_finder -c "\d <table_name>"
```

## Folder structure

```
backend/
├── app/
│   ├── api/            FastAPI route handlers
│   ├── core/            Config, security
│   ├── db/               Session, queries, base
│   ├── models/          SQLAlchemy ORM models (hand-synced with migrations — see above)
│   ├── graph_engine/    NetworkX routing logic (has its own tests/)
│   └── main.py
├── migrations/          Alembic migration scripts
├── tests/                DB-backed integration tests
├── .env.example
├── alembic.ini
├── Dockerfile
└── requirements.txt
```