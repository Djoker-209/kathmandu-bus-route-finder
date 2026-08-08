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
# ADMIN_API_KEY and JWT_SECRET_KEY have no defaults in the app itself --
# generate real values for local dev:
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Python environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Apply migrations (creates stops / routes / route_stops / etc.)
alembic upgrade head

# 5. Seed the first admin account (needed for POST /admin/login --
# there's no self-registration endpoint)
python3 -m scripts.seed_admin

# 6. (Optional) Road-network route geometry via OSRM
# Without this, /route-finder still works correctly -- it just returns
# road_geometry: null on every leg, and the frontend falls back to
# straight-line segments between stops.
#
# One-time data prep (only re-run if nepal-latest.osm.pbf changes):
wget http://download.geofabrik.de/asia/nepal-latest.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/nepal-latest.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/nepal-latest.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/nepal-latest.osrm

# Start the OSRM router (managed via docker-compose, from repo root):
cd ..
docker compose up -d osrm
cd backend
# Runs on http://localhost:5000, restarts automatically on reboot
# (restart: unless-stopped). No need to manually start it again after
# the first time unless you stop it explicitly.

# 7. Run the API
uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000` (interactive docs at `/docs`).

## Admin API

Two separate auth mechanisms, for two separate purposes:

- **`X-Admin-Api-Key` header** (`ADMIN_API_KEY` in `.env`) — gates the
  data-entry endpoints in `app/api/admin.py`: `POST /stops`, `POST /routes`,
  `POST /routes/{route_id}/stops`, `POST /graph/reload`, and
  `POST /admin/rebuild-graph` (in `main.py`). One shared secret for the
  small team doing data entry — not per-user.
- **JWT via `POST /admin/login`** — authenticates an `AdminUser` account
  (seeded with `python3 -m scripts.seed_admin`, see Setup step 5) and
  returns a bearer token. Not currently required by anything in
  `admin.py` — the two systems coexist; `admin.py`'s endpoints still use
  the shared key.

`stop_id`/`route_id` for newly created rows are server-generated, not
caller-supplied: stops get the next sequential `S####` value, routes get
a reserved `M######` prefix (kept separate from the existing `R`-number
space, which is OSM-sourced and not sequential — see
`app/db/id_generator.py`).

`routes.operator_id` can legitimately be `NULL` — this isn't a data bug.
Some routes are run by informal/unregistered local microbus services with
no known formal operator; for these, `operator_id` is left null while the
free-text `operator` column (e.g. "Local Microbus") still describes who
runs it. Don't assume a null `operator_id` means missing data that needs
fixing — check `operator` first before treating it as an issue.

## Running tests

```bash
pytest -v
```

Some tests in `tests/` (e.g. `test_stops.py`) require a live database and will skip cleanly if one isn't reachable — make sure `docker compose up -d db` has been run first and migrations are applied, or those tests will just no-op.

Routing/pathfinder unit tests live in `tests/test_routing.py`.

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
│   ├── core/            Config, security (shared-key + JWT auth)
│   ├── db/               Session, queries, id_generator, base
│   ├── models/          SQLAlchemy ORM models (hand-synced with migrations — see above)
│   ├── routing/          NetworkX routing logic (graph_builder, pathfinder, constants)
│   └── main.py
├── migrations/          Alembic migration scripts
├── scripts/              One-off admin scripts (e.g. seed_admin.py)
├── tests/                DB-backed integration tests + routing unit tests
├── .env.example
├── alembic.ini
├── Dockerfile
└── requirements.txt
```
