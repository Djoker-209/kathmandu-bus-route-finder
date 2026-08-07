# Source Code Export

This document contains the current source and configuration files of the project.

## File Index

## .github/workflows/ci.yml

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.4
        env:
          POSTGRES_USER: ktm_bus
          POSTGRES_PASSWORD: ktm_bus_dev
          POSTGRES_DB: ktm_bus_route_finder
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest

  frontend-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install & test (if frontend is scaffolded)
        run: |
          if [ -f package.json ]; then
            npm install
            npm test --if-present
          else
            echo "Frontend not yet scaffolded — skipping."
          fi
```

## CONTRIBUTING.md

```markdown
# Contributing — Team Workflow

Three people, one repo. This doc is the actual day-to-day loop: how to get set up, how to make a change without stepping on each other, and how to merge safely.

## Ownership (avoids most conflicts before they happen)

| Area | Owner | Folder |
|---|---|---|
| Schema, data pipeline, spatial queries, data access layer | **Dipesh** | `backend/app/db/`, `backend/migrations/`, `data/` |
| Graph engine, Dijkstra/BFS, FastAPI route endpoints | **Janak** | `backend/app/api/`, `backend/app/core/` |
| UI, map, Leaflet/OSRM integration | **Dinesh** | `frontend/` |

You'll still touch each other's folders sometimes (e.g. Janak's graph engine needs Dipesh's `get_nearest_stop()` function) — that's fine, just open a PR like normal so the owner sees the change.

## One-time setup (each person, once)

```bash
git clone https://github.com/<username>/kathmandu-bus-route-finder.git
cd kathmandu-bus-route-finder

# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
cd ..

# Frontend (once Dinesh scaffolds it)
cd frontend
npm install
cd ..

# Database
docker compose up -d db
cd backend && alembic upgrade head && cd ..
```

## Daily workflow loop

1. **Start from a clean, up-to-date `main`:**
```bash
   git checkout main
   git pull origin main
```

2. **Create a branch per task** — name it after the Jira/Scrum ticket so it's traceable:
```bash
   git checkout -b scrum-3/dedup-stops
```
   Convention: `<scrum-number>/<short-description>` (e.g. `scrum-5/data-access-layer`, `scrum-6-graph/dijkstra-tests`).

3. **Work, commit in small chunks:**
```bash
   git add <files>
   git commit -m "Scrum 3: add 30m distance-based stop deduplication"
```
   If you're linking Jira, prefix with the issue key so Jira picks it up automatically (e.g. `KTM-14: add dedup script`).

4. **Run tests before pushing — every time:**
```bash
   cd backend && pytest
   cd ../frontend && npm test --if-present
```

5. **Push and open a PR:**
```bash
   git push -u origin scrum-3/dedup-stops
```
   Then on GitHub: **Compare & pull request** → target `main` → tag one teammate as reviewer.

6. **Reviewer checks it, approves or comments.** CI (`.github/workflows/ci.yml`) also has to pass — it spins up a real Postgres/PostGIS container and runs `pytest` automatically on every PR.

7. **Merge** (use "Squash and merge" to keep `main`'s history one-commit-per-feature and readable for your report/viva).

8. **Delete the branch** after merge, and everyone else runs `git pull origin main` before starting their next task.

## The one place conflicts actually hurt: the database schema

Only **one migration chain** can exist. If two people add migrations at the same time off the same `main`, the second person to push will need to rebase:

```bash
git checkout main && git pull
git checkout your-branch
git rebase main
# fix the migration numbering/down_revision if alembic complains
alembic upgrade head   # test it applies cleanly
```

Rule of thumb: **whoever is working on `backend/migrations/` at a given moment should say so in your team chat** before starting, so you don't both generate migration `0002` at once. This is Dipesh's area, so in practice Janak/Dinesh should ping before touching it.

## Keeping everyone's local DB in sync

Whenever you pull `main` and it includes a new migration:
```bash
cd backend
alembic upgrade head
```
That's it — your local Postgres container catches up automatically.

## Quick reference

```bash
git checkout main && git pull          # sync
git checkout -b scrum-X/task-name      # new branch per task
# ...work, test...
git push -u origin scrum-X/task-name   # push
# open PR on GitHub, get review, squash-merge
git checkout main && git pull          # sync again before next task
```
```

## README.md

```markdown
# Kathmandu Bus Route Finder

A web-based public transport navigation system for the Kathmandu Valley. Enter an origin and destination and get a direct or single-transfer bus route, rendered on an interactive map.

BE Minor Project — Department of Electronics & Computer Engineering, IOE Pulchowk Campus.

**Team:** Dinesh Bhatta (080BCT025) · Dipesh S Saud (080BCT026) · Janak S Pujara (080BCT035)

## Repo layout

```
backend/     FastAPI + NetworkX (graph engine) + PostGIS data access layer
frontend/    Next.js 14 + Leaflet.js map UI
data/        Raw exports, cleaned dataset, ETL scripts
docs/        Proposal, defense materials, diagrams
```

## Tech stack

| Layer      | Tech                                  |
|------------|----------------------------------------|
| Frontend   | Next.js 14, TypeScript, Tailwind CSS, Leaflet.js |
| Backend    | Python 3.11, FastAPI, NetworkX, Pydantic |
| Database   | PostgreSQL 15 + PostGIS                |
| Routing    | OSRM (road-network geometry)           |

## Local development

```bash
# 1. Start Postgres + PostGIS
docker compose up -d db

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head        # creates stops / routes / route_stops
uvicorn app.main:app --reload

# 3. Frontend
cd frontend
npm install
npm run dev
```

Backend runs at `http://localhost:8000` (docs at `/docs`). Frontend runs at `http://localhost:3000`.

## Database migrations

Schema changes are tracked with Alembic (`backend/migrations/`), per the reproducibility requirement in the proposal (Section 5.5.4).

```bash
cd backend
alembic upgrade head                          # apply all migrations
alembic revision -m "add fare column"          # create a new migration
alembic downgrade -1                           # roll back one step
```

## Team task boards

Tracked in Jira (Scrum board, 3 sprints, 7 epics). See `docs/` for the project proposal and Gantt schedule.

## Graph engine (backend/app/graph_engine)

The `graph_engine` package builds an in-memory transport graph and
provides a `RouteFinder` to query shortest-paths (direct or single transfer). The package was refactored to improve imports, docstrings, and testability. Unit tests live under `backend/app/graph_engine/tests`.

```powershell
.\venv\Scripts\python.exe -m pytest -q backend/app/graph_engine
```

Run the tests:

```powershell
.\venv\Scripts\python.exe -m pytest -q backend/app/graph_engine
```
```

## backend/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## backend/alembic.ini

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

## backend/app/__init__.py

```python

```

## backend/app/api/__init__.py

```python

```

## backend/app/core/__init__.py

```python

```

## backend/app/core/config.py

```python
"""
Application configuration.

Loads settings from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # ---------------------------------------
    # Database
    # ---------------------------------------

    DATABASE_URL: str

    # ---------------------------------------
    # JWT Authentication
    # ---------------------------------------

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ---------------------------------------
    # FastAPI
    # ---------------------------------------

    PROJECT_NAME: str = "Kathmandu Bus Route API"

    API_VERSION: str = "1.0.0"

    DEBUG: bool = False

    # ---------------------------------------
    # Pydantic Configuration
    # ---------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
```

## backend/app/core/security.py

```python
"""
Authentication and authorization utilities.

This module provides:

- Password hashing
- Password verification
- JWT creation
- JWT validation
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import AdminUser

# --------------------------------------------------
# Password Hashing
# --------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# --------------------------------------------------
# OAuth2
# --------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/admin/login"
)

# --------------------------------------------------
# Password Functions
# --------------------------------------------------

def hash_password(password: str) -> str:
    """
    Hash a plain-text password.
    """
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )

# --------------------------------------------------
# JWT Functions
# --------------------------------------------------

def create_access_token(
    subject: str,
) -> str:
    """
    Create a signed JWT access token.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_access_token(
    token: str,
) -> str:
    """
    Decode and validate a JWT.

    Returns
    -------
    str
        Username stored in the token.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        return username

    except JWTError:
        raise credentials_exception

# --------------------------------------------------
# Current Logged-in Admin
# --------------------------------------------------

def get_current_admin(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> AdminUser:
    """
    Return the authenticated administrator.
    """

    username = verify_access_token(token)

    admin = (
        db.query(AdminUser)
        .filter(
            AdminUser.username == username
        )
        .first()
    )

    if admin is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator not found",
        )

    return admin
```

## backend/app/db/__init__.py

```python

```

## backend/app/db/base.py

```python
"""
Import all ORM models so that SQLAlchemy and Alembic
can discover them through Base.metadata.
"""

from app.models import (
    AdminUser,
    Base,
    Route,
    RouteStop,
    Stop,
)

__all__ = [
    "Base",
    "Stop",
    "Route",
    "RouteStop",
    "AdminUser",
]
```

## backend/app/db/graph_loader.py

```python
"""
Load routing data from PostgreSQL and build the in-memory graph.

This module converts SQLAlchemy ORM models into the graph_engine
dataclasses and constructs the routing graph used by RouteFinder.
"""

from sqlalchemy.orm import Session

from app.graph_engine.graph_builder import build_graph
from app.graph_engine.models import (
    RouteStop as GraphRouteStop,
    Stop as GraphStop,
)

from app.models import RouteStop, Stop


def load_graph(db: Session):
    """
    Load all routing data from the database and
    build the graph.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy database session.

    Returns
    -------
    dict
        Graph produced by graph_builder.build_graph().
    """

    # ------------------------------------------
    # Read all stops
    # ------------------------------------------

    db_stops = db.query(Stop).all()

    graph_stops = {
        stop.stop_id: GraphStop(
            stop_id=stop.stop_id,
            name=stop.stop_name,
            latitude=stop.latitude,
            longitude=stop.longitude,
        )
        for stop in db_stops
    }

    # ------------------------------------------
    # Read all route-stop mappings
    # ------------------------------------------

    db_route_stops = (
        db.query(RouteStop)
        .order_by(
            RouteStop.route_id,
            RouteStop.sequence,
        )
        .all()
    )

    graph_route_stops = [
        GraphRouteStop(
            route_id=rs.route_id,
            stop_id=rs.stop_id,
            sequence=rs.sequence,
        )
        for rs in db_route_stops
    ]

    # ------------------------------------------
    # Build graph
    # ------------------------------------------

    graph = build_graph(
        graph_stops,
        graph_route_stops,
    )

    return graph
```

## backend/app/db/schema.sql

```sql
-- Kathmandu Bus Route Finder — Normalized schema (REFERENCE COPY)
-- Scrum 1: stops, routes, route_stops + PostGIS spatial indexes
--
-- NOTE: The source of truth is now backend/migrations/versions/0001_initial_schema.py
-- (Alembic). This file is kept as a plain-SQL reference for quick reading / manual
-- psql inspection. If you change the schema, update the Alembic migration, then
-- regenerate this file to match (or just delete this file to avoid drift).

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- stops
-- ============================================================
CREATE TABLE IF NOT EXISTS stops (
    stop_id         SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    name_normalized VARCHAR(150) NOT NULL,       -- lowercase, trimmed, for dedup/search
    is_interchange  BOOLEAN NOT NULL DEFAULT FALSE,
    geom            GEOMETRY(Point, 4326) NOT NULL,
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_stops_geom ON stops USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_stops_name_normalized ON stops (name_normalized);

-- ============================================================
-- routes
-- ============================================================
CREATE TABLE IF NOT EXISTS routes (
    route_id        SERIAL PRIMARY KEY,
    route_number    VARCHAR(20) NOT NULL,
    route_name      VARCHAR(150) NOT NULL,
    operator        VARCHAR(100),
    tier            SMALLINT CHECK (tier IN (1, 2, 3)),   -- Tier 1/2/3 per proposal Sec 5.5.1
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    source          VARCHAR(50),                          -- e.g. 'DOTM', 'OSM', 'field_survey'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_routes_tier ON routes (tier);
CREATE INDEX IF NOT EXISTS idx_routes_verified ON routes (verified);

-- ============================================================
-- route_stops (join table — ordered stop sequence per route)
-- ============================================================
CREATE TABLE IF NOT EXISTS route_stops (
    route_id        INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    stop_id         INTEGER NOT NULL REFERENCES stops(stop_id) ON DELETE CASCADE,
    sequence_order  INTEGER NOT NULL,                     -- 1-indexed position along the route
    PRIMARY KEY (route_id, sequence_order)
);

CREATE INDEX IF NOT EXISTS idx_route_stops_route_id ON route_stops (route_id);
CREATE INDEX IF NOT EXISTS idx_route_stops_stop_id ON route_stops (stop_id);

-- Ensures a stop can't repeat at two different positions on the same route
CREATE UNIQUE INDEX IF NOT EXISTS uq_route_stop_position
    ON route_stops (route_id, stop_id, sequence_order);
```

## backend/app/db/session.py

```python
"""
Database engine and session configuration.

This module is responsible for:

- Creating the SQLAlchemy engine.
- Creating database sessions.
- Providing a FastAPI dependency for database access.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# -------------------------------------------------
# SQLAlchemy Engine
# -------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)


# -------------------------------------------------
# Session Factory
# -------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# -------------------------------------------------
# FastAPI Dependency
# -------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Create a database session for each request.

    The session is automatically closed
    after the request finishes.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
```

## backend/app/graph_engine/__init__.py

```python
"""graph_engine public API."""

from .graph_builder import build_graph
from .route_finder import RouteFinder

__all__ = ["build_graph", "RouteFinder"]
```

## backend/app/graph_engine/constants.py

```python
"""Small set of tunable constants (meters)."""

EARTH_RADIUS: int = 6_371_000
INTERCHANGE_DISTANCE: int = 100
TRANSFER_PENALTY: int = 900
```

## backend/app/graph_engine/graph_builder.py

```python
"""Graph construction utilities.

This module builds a single directed, weighted graph representing the
city bus network. Node IDs are `stop_id` values. Two edge kinds are
present:

- "route": connects consecutive stops on the same route; weight is
  the geographic distance in metres.
- "transfer": connects geographically close stops from different
  routes and has an added transfer penalty to reflect walking + wait
  overhead.
"""

from collections import defaultdict
from itertools import combinations
from typing import Dict, Iterable

import networkx as nx

from .models import RouteStop, Stop
from .utils import haversine_distance
from .constants import TRANSFER_PENALTY, INTERCHANGE_DISTANCE


# Edge type markers stored on graph edges
EDGE_TYPE_ROUTE = "route"
EDGE_TYPE_TRANSFER = "transfer"


def build_graph(stops: Iterable[Stop], route_stops: Iterable[RouteStop]) -> nx.DiGraph:
    """Construct and return a directed NetworkX graph for the network.

    Args:
        stops: iterable of `Stop` objects describing known stops.
        route_stops: iterable of `RouteStop` objects describing which
            stops belong to which route and their sequence.

    Returns:
        A `networkx.DiGraph` where node IDs are `stop_id` and edges
        have attributes `weight`, `edge_type` and optionally `route_id`.
    """

    graph = nx.DiGraph()

    stops_by_id: Dict[int, Stop] = {s.stop_id: s for s in stops}
    for stop in stops:
        graph.add_node(stop.stop_id, name=stop.name, lat=stop.lat, lng=stop.lng)

    _add_route_edges(graph, stops_by_id, list(route_stops))
    _add_transfer_edges(graph, stops_by_id, list(route_stops))

    return graph


def _add_route_edges(graph: nx.DiGraph, stops_by_id: Dict[int, Stop], route_stops: list[RouteStop]) -> None:
    """Connect consecutive stops within each route in both directions.

    The graph treats routes as bidirectional by default. If your source
    data contained directionality, adjust this function accordingly.
    """
    by_route: dict[int, list[RouteStop]] = defaultdict(list)
    for rs in route_stops:
        by_route[rs.route_id].append(rs)

    for route_id, stops_in_route in by_route.items():
        stops_in_route.sort(key=lambda rs: rs.sequence_order)
        for a, b in zip(stops_in_route, stops_in_route[1:]):
            # Ignore incomplete references (defensive programming)
            if a.stop_id not in stops_by_id or b.stop_id not in stops_by_id:
                continue

            stop_a, stop_b = stops_by_id[a.stop_id], stops_by_id[b.stop_id]
            dist = haversine_distance(stop_a.lat, stop_a.lng, stop_b.lat, stop_b.lng)
            graph.add_edge(a.stop_id, b.stop_id, weight=dist, edge_type=EDGE_TYPE_ROUTE, route_id=route_id)
            graph.add_edge(b.stop_id, a.stop_id, weight=dist, edge_type=EDGE_TYPE_ROUTE, route_id=route_id)


def _add_transfer_edges(graph: nx.DiGraph, stops_by_id: Dict[int, Stop], route_stops: list[RouteStop]) -> None:
    """Add transfer edges between geographically close stops on
    different routes.

    A transfer edge's weight is the geographic distance plus a fixed
    penalty to approximate walk + wait time.
    """
    stop_to_routes: dict[int, set[int]] = defaultdict(set)
    for rs in route_stops:
        stop_to_routes[rs.stop_id].add(rs.route_id)

    stop_ids = list(stop_to_routes.keys())
    for id_a, id_b in combinations(stop_ids, 2):
        # Skip if they already share a route -- then no transfer is needed.
        if stop_to_routes[id_a] & stop_to_routes[id_b]:
            continue

        # Defensive: ensure both stops exist in the provided stop list.
        if id_a not in stops_by_id or id_b not in stops_by_id:
            continue

        stop_a, stop_b = stops_by_id[id_a], stops_by_id[id_b]
        dist = haversine_distance(stop_a.lat, stop_a.lng, stop_b.lat, stop_b.lng)

        if dist <= INTERCHANGE_DISTANCE:
            weight = dist + TRANSFER_PENALTY
            graph.add_edge(id_a, id_b, weight=weight, edge_type=EDGE_TYPE_TRANSFER)
            graph.add_edge(id_b, id_a, weight=weight, edge_type=EDGE_TYPE_TRANSFER)
```

## backend/app/graph_engine/models.py

```python
"""Data shapes used by the graph engine."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stop:
    stop_id: int
    name: str
    lat: float
    lng: float


@dataclass(frozen=True)
class RouteStop:
    route_id: int
    stop_id: int
    sequence_order: int
```

## backend/app/graph_engine/requirements.txt

```text
��a n n o t a t e d - d o c = = 0 . 0 . 5 
 
 a n n o t a t e d - t y p e s = = 0 . 8 . 0 
 
 a n y i o = = 4 . 1 4 . 2 
 
 a s t t o k e n s = = 3 . 0 . 2 
 
 c f f i = = 2 . 1 . 0 
 
 c o l o r a m a = = 0 . 4 . 6 
 
 c o m m = = 0 . 2 . 3 
 
 c r y p t o g r a p h y = = 5 0 . 0 . 0 
 
 d e b u g p y = = 1 . 8 . 2 1 
 
 d e c o r a t o r = = 5 . 3 . 1 
 
 e c d s a = = 0 . 1 9 . 2 
 
 e x e c u t i n g = = 2 . 2 . 1 
 
 f a s t a p i = = 0 . 1 4 1 . 1 
 
 g r e e n l e t = = 3 . 5 . 4 
 
 i d n a = = 3 . 1 8 
 
 i n i c o n f i g = = 2 . 3 . 0 
 
 i p y k e r n e l = = 7 . 3 . 0 
 
 i p y t h o n = = 9 . 1 5 . 0 
 
 i p y t h o n _ p y g m e n t s _ l e x e r s = = 1 . 1 . 1 
 
 j e d i = = 0 . 2 0 . 0 
 
 j o s e = = 1 . 0 . 0 
 
 j u p y t e r _ c l i e n t = = 8 . 9 . 1 
 
 j u p y t e r _ c o r e = = 5 . 9 . 1 
 
 m a t p l o t l i b - i n l i n e = = 0 . 2 . 2 
 
 n e s t - a s y n c i o 2 = = 1 . 7 . 2 
 
 n e t w o r k x = = 3 . 6 . 1 
 
 p a c k a g i n g = = 2 6 . 2 
 
 p a r s o = = 0 . 8 . 7 
 
 p a s s l i b = = 1 . 7 . 4 
 
 p l a t f o r m d i r s = = 4 . 1 1 . 0 
 
 p l u g g y = = 1 . 6 . 0 
 
 p r o m p t _ t o o l k i t = = 3 . 0 . 5 3 
 
 p s u t i l = = 7 . 2 . 2 
 
 p u r e _ e v a l = = 0 . 2 . 3 
 
 p y a s n 1 = = 0 . 6 . 4 
 
 p y c p a r s e r = = 3 . 0 
 
 p y d a n t i c = = 2 . 1 3 . 4 
 
 p y d a n t i c - s e t t i n g s = = 2 . 1 4 . 2 
 
 p y d a n t i c _ c o r e = = 2 . 4 6 . 4 
 
 P y g m e n t s = = 2 . 2 0 . 0 
 
 p y t e s t = = 9 . 1 . 1 
 
 p y t h o n - d a t e u t i l = = 2 . 9 . 0 . p o s t 0 
 
 p y t h o n - d o t e n v = = 1 . 2 . 2 
 
 p y t h o n - j o s e = = 3 . 5 . 0 
 
 p y z m q = = 2 7 . 1 . 0 
 
 r s a = = 4 . 9 . 1 
 
 s i x = = 1 . 1 7 . 0 
 
 S Q L A l c h e m y = = 2 . 0 . 5 1 
 
 s t a c k - d a t a = = 0 . 6 . 3 
 
 s t a r l e t t e = = 1 . 3 . 1 
 
 t o r n a d o = = 6 . 5 . 7 
 
 t r a i t l e t s = = 5 . 1 5 . 1 
 
 t y p i n g - i n s p e c t i o n = = 0 . 4 . 2 
 
 t y p i n g _ e x t e n s i o n s = = 4 . 1 6 . 0 
 
 w c w i d t h = = 0 . 8 . 2 
 
 
```

## backend/app/graph_engine/route_finder.py

```python
"""Shortest-path helpers for the transport graph."""

from dataclasses import dataclass
from typing import List, Optional

import networkx as nx


class NoRouteFoundError(Exception):
    pass


@dataclass
class RouteResult:
    stop_ids: List[int]
    total_weight: float
    is_transfer: bool
    transfer_stop_id: Optional[int]


class RouteFinder:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def find_route(self, source_stop_id: int, dest_stop_id: int) -> RouteResult:
        self._validate_nodes(source_stop_id, dest_stop_id)
        try:
            path = nx.dijkstra_path(self.graph, source_stop_id, dest_stop_id, weight="weight")
            total_weight = nx.dijkstra_path_length(self.graph, source_stop_id, dest_stop_id, weight="weight")
        except nx.NetworkXNoPath as exc:
            raise NoRouteFoundError(f"No route between {source_stop_id} and {dest_stop_id}") from exc
        transfer_stop_id = self._first_transfer_edge_target(path)
        return RouteResult(stop_ids=path, total_weight=total_weight, is_transfer=transfer_stop_id is not None, transfer_stop_id=transfer_stop_id)

    def find_route_bfs(self, source_stop_id: int, dest_stop_id: int) -> RouteResult:
        self._validate_nodes(source_stop_id, dest_stop_id)
        try:
            path = nx.shortest_path(self.graph, source_stop_id, dest_stop_id)
        except nx.NetworkXNoPath as exc:
            raise NoRouteFoundError(f"No route between {source_stop_id} and {dest_stop_id}") from exc
        return RouteResult(stop_ids=path, total_weight=float(len(path) - 1), is_transfer=False, transfer_stop_id=None)

    def _first_transfer_edge_target(self, path: List[int]) -> Optional[int]:
        for a, b in zip(path, path[1:]):
            if self.graph.edges[a, b].get("edge_type") == "transfer":
                return b
        return None

    def _validate_nodes(self, source_stop_id: int, dest_stop_id: int) -> None:
        if source_stop_id == dest_stop_id:
            raise ValueError("Source and destination stops are identical.")
        if source_stop_id not in self.graph:
            raise NoRouteFoundError(f"Unknown source stop: {source_stop_id}")
        if dest_stop_id not in self.graph:
            raise NoRouteFoundError(f"Unknown destination stop: {dest_stop_id}")
```

## backend/app/graph_engine/sample_data.py

```python
"""
sample_data.py

A miniature Kathmandu network that stands in for the database until
BRF-6 (real data collection) is done. Coordinates below are verified
via web search against real-world sources, not guessed -- this matters
because a wrong coordinate silently produces a wrong distance, which
silently produces a wrong route.

Network:

  Route 1 "Ratnapark - Tripureshwor" (the example corridor):
      Ratnapark -> New Road -> Tripureshwor

  Route 2 "Tripureshwor - Kalanki":
      Tripureshwor -> Kalanki

  Tripureshwor is a real, well-known interchange point in Kathmandu
  (it sits on the Ring Road), so it's used here deliberately -- Route 1
  and Route 2 each have their OWN "Tripureshwor" stop row, about 40m
  apart, exactly like two different operators' independently-collected
  stop pins for the same real place. This is what tests whether the
  proximity-based interchange detection actually works, not just
  whether the code runs.

  Budhanilkantha is included as a deliberately disconnected stop, for
  the "no route exists" edge case.
"""
"""Compact sample network for tests and demos."""

from .models import RouteStop, Stop


STOPS = [
    # --- Route 1: Ratnapark -> New Road -> Tripureshwor ---
    Stop(1, "Ratnapark", 27.7075, 85.3155),
    Stop(2, "New Road", 27.7020, 85.3074),
    Stop(3, "Tripureshwor (Rt.1 stop)", 27.6953, 85.3130),

    # --- Route 2: Tripureshwor -> Kalanki ---
    # Same real-world location as stop 3, ~40m away.
    Stop(4, "Tripureshwor (Rt.2 stop)", 27.6950, 85.3128),
    Stop(5, "Kalanki", 27.6939, 85.2803),  # approx, intermediate/endpoint

    # --- Deliberately disconnected ---
    Stop(99, "Budhanilkantha", 27.7807, 85.3617),
]


ROUTE_STOPS = [
    RouteStop(route_id=1, stop_id=1, sequence_order=1),
    RouteStop(route_id=1, stop_id=2, sequence_order=2),
    RouteStop(route_id=1, stop_id=3, sequence_order=3),

    RouteStop(route_id=2, stop_id=4, sequence_order=1),
    RouteStop(route_id=2, stop_id=5, sequence_order=2),
]
```

## backend/app/graph_engine/tests/__init__.py

```python

```

## backend/app/graph_engine/tests/test_graph_builder.py

```python
"""Tests for graph_builder.py — nodes, route edges, and transfer edges."""
from app.graph_engine.models import RouteStop, Stop
from app.graph_engine.graph_builder import build_graph
from app.graph_engine.constants import TRANSFER_PENALTY

# Small hand-built network, independent of sample_data.py, so this
# test doesn't silently break if the sample data changes later.
STOPS = [
    Stop(1, "A", 27.700, 85.300),
    Stop(2, "B", 27.701, 85.301),
    Stop(3, "C", 27.702, 85.302),   # close to stop 4 -> interchange
    Stop(4, "D", 27.7021, 85.3021),  # ~50m from stop 3
]
ROUTE_STOPS = [
    RouteStop(route_id=1, stop_id=1, sequence_order=1),
    RouteStop(route_id=1, stop_id=2, sequence_order=2),
    RouteStop(route_id=1, stop_id=3, sequence_order=3),
    RouteStop(route_id=2, stop_id=4, sequence_order=1),
]


def test_all_stops_become_nodes():
    graph = build_graph(STOPS, ROUTE_STOPS)
    assert graph.number_of_nodes() == len(STOPS)


def test_route_edges_connect_consecutive_stops_both_directions():
    graph = build_graph(STOPS, ROUTE_STOPS)
    assert graph.has_edge(1, 2)
    assert graph.has_edge(2, 1)
    assert graph[1][2]["edge_type"] == "route"


def test_transfer_edge_created_between_nearby_different_route_stops():
    graph = build_graph(STOPS, ROUTE_STOPS)
    assert graph.has_edge(3, 4)
    assert graph[3][4]["edge_type"] == "transfer"


def test_transfer_edge_weight_includes_penalty():
    graph = build_graph(STOPS, ROUTE_STOPS)
    transfer_weight = graph[3][4]["weight"]
    # The transfer weight must be at least the penalty -- if it isn't,
    # the penalty isn't actually being applied.
    assert transfer_weight >= TRANSFER_PENALTY


def test_no_transfer_edge_between_same_route_stops():
    graph = build_graph(STOPS, ROUTE_STOPS)
    # stops 1 and 3 are on the same route -- no transfer edge needed
    # (they're already connected via route edges through stop 2)
    assert graph.get_edge_data(1, 3) is None
```

## backend/app/graph_engine/tests/test_graph_engine.py

```python
"""End-to-end tests for the graph engine.

These tests exercise the full pipeline: sample data -> graph builder ->
RouteFinder. They check direct and transfer routes, ensure edge weights
are sane, and validate node attributes expected by downstream code.
"""
import pytest

from app.graph_engine import build_graph, RouteFinder
from app.graph_engine.sample_data import STOPS, ROUTE_STOPS
from app.graph_engine.route_finder import NoRouteFoundError


def test_full_engine_smoke():
	graph = build_graph(STOPS, ROUTE_STOPS)
	finder = RouteFinder(graph)

	# Direct route: Ratnapark (1) -> Tripureshwor (3) via New Road (2)
	res = finder.find_route(1, 3)
	assert res.stop_ids == [1, 2, 3]
	assert res.is_transfer is False

	# Transfer route: Ratnapark (1) -> Kalanki (5) via Tripureshwor
	res2 = finder.find_route(1, 5)
	assert res2.stop_ids[0] == 1
	assert res2.stop_ids[-1] == 5
	assert res2.is_transfer is True
	assert res2.transfer_stop_id == 4

	# No route exists to isolated stop 99
	with pytest.raises(NoRouteFoundError):
		finder.find_route(1, 99)


def test_graph_sanity_checks():
	graph = build_graph(STOPS, ROUTE_STOPS)

	# Nodes include lat/lng metadata
	for node, data in graph.nodes(data=True):
		assert "lat" in data and "lng" in data

	# All edge weights are non-negative and transfer edges exist
	transfer_found = False
	for u, v, data in graph.edges(data=True):
		assert data.get("weight", 0) >= 0
		if data.get("edge_type") == "transfer":
			transfer_found = True
	assert transfer_found


def test_bfs_vs_dijkstra_on_direct_route():
	graph = build_graph(STOPS, ROUTE_STOPS)
	finder = RouteFinder(graph)

	dij = finder.find_route(1, 3)
	bfs = finder.find_route_bfs(1, 3)
	assert dij.stop_ids == bfs.stop_ids
```

## backend/app/graph_engine/tests/test_integration.py

```python
"""
Whole-workflow integration test: sample_data -> models -> graph_builder
-> route_finder, exercised end to end exactly as the real API endpoint
will use it later (Phase 10). If this file passes, the entire graph
engine works together, not just in isolated pieces.
"""
from app.graph_engine import build_graph, RouteFinder
from app.graph_engine.sample_data import ROUTE_STOPS, STOPS


def test_full_pipeline_direct_route():
    graph = build_graph(STOPS, ROUTE_STOPS)
    finder = RouteFinder(graph)

    result = finder.find_route(1, 3)  # Ratnapark -> Tripureshwor (Rt.1)

    assert result.stop_ids == [1, 2, 3]
    assert result.is_transfer is False
    assert result.total_weight > 0


def test_full_pipeline_transfer_route():
    graph = build_graph(STOPS, ROUTE_STOPS)
    finder = RouteFinder(graph)

    result = finder.find_route(1, 5)  # Ratnapark -> Kalanki

    assert result.stop_ids[0] == 1
    assert result.stop_ids[-1] == 5
    assert result.is_transfer is True
    assert result.transfer_stop_id == 4  # Tripureshwor (Rt.2 stop)


def test_full_pipeline_no_route_to_isolated_stop():
    from app.graph_engine.route_finder import NoRouteFoundError
    import pytest

    graph = build_graph(STOPS, ROUTE_STOPS)
    finder = RouteFinder(graph)

    with pytest.raises(NoRouteFoundError):
        finder.find_route(1, 99)  # Budhanilkantha, deliberately isolated
```

## backend/app/graph_engine/tests/test_models.py

```python
"""Tests for models.py — do the dataclasses hold and expose values correctly."""
from app.graph_engine.models import RouteStop, Stop


def test_stop_holds_values_correctly():
    s = Stop(1, "Ratnapark", 27.7075, 85.3155)
    assert s.stop_id == 1
    assert s.name == "Ratnapark"
    assert s.lat == 27.7075
    assert s.lng == 85.3155


def test_route_stop_holds_values_correctly():
    rs = RouteStop(route_id=1, stop_id=1, sequence_order=1)
    assert rs.route_id == 1
    assert rs.stop_id == 1
    assert rs.sequence_order == 1


def test_stop_is_immutable():
    """Stops are frozen dataclasses -- accidental mutation should fail
    loudly, not silently corrupt the graph later."""
    s = Stop(1, "Ratnapark", 27.7075, 85.3155)
    try:
        s.lat = 0.0
        assert False, "Stop should be immutable (frozen=True)"
    except AttributeError:
        pass
```

## backend/app/graph_engine/tests/test_route_finder.py

```python
"""Tests for route_finder.py — Dijkstra (primary) and BFS (comparator)."""
import pytest

from app.graph_engine.graph_builder import build_graph
from app.graph_engine.models import RouteStop, Stop
from app.graph_engine.route_finder import NoRouteFoundError, RouteFinder

STOPS = [
    Stop(1, "A", 27.700, 85.300),
    Stop(2, "B", 27.701, 85.301),
    Stop(3, "C", 27.702, 85.302),
    Stop(4, "D", 27.7021, 85.3021),  # interchange with C
    Stop(5, "E", 27.703, 85.303),
    Stop(99, "Isolated", 27.750, 85.350),
]
ROUTE_STOPS = [
    RouteStop(route_id=1, stop_id=1, sequence_order=1),
    RouteStop(route_id=1, stop_id=2, sequence_order=2),
    RouteStop(route_id=1, stop_id=3, sequence_order=3),
    RouteStop(route_id=2, stop_id=4, sequence_order=1),
    RouteStop(route_id=2, stop_id=5, sequence_order=2),
]


@pytest.fixture
def finder() -> RouteFinder:
    return RouteFinder(build_graph(STOPS, ROUTE_STOPS))


def test_direct_route(finder):
    result = finder.find_route(1, 3)
    assert result.stop_ids == [1, 2, 3]
    assert result.is_transfer is False


def test_transfer_route(finder):
    result = finder.find_route(1, 5)
    assert result.is_transfer is True
    assert result.transfer_stop_id == 4


def test_no_route_to_isolated_stop(finder):
    with pytest.raises(NoRouteFoundError):
        finder.find_route(1, 99)


def test_same_source_and_destination_raises(finder):
    with pytest.raises(ValueError):
        finder.find_route(1, 1)


def test_bfs_matches_dijkstra_on_direct_route(finder):
    dijkstra_result = finder.find_route(1, 3)
    bfs_result = finder.find_route_bfs(1, 3)
    assert dijkstra_result.stop_ids == bfs_result.stop_ids
```

## backend/app/graph_engine/tests/test_sample_data.py

```python
"""Tests for sample_data.py — is the miniature Kathmandu network well-formed."""
from app.graph_engine.sample_data import STOPS, ROUTE_STOPS
from app.graph_engine.utils import haversine_distance
from app.graph_engine.constants import INTERCHANGE_DISTANCE


def test_has_at_least_two_routes():
    route_ids = {rs.route_id for rs in ROUTE_STOPS}
    assert len(route_ids) >= 2


def test_has_a_disconnected_stop_for_edge_case_testing():
    connected_ids = {rs.stop_id for rs in ROUTE_STOPS}
    disconnected = [s for s in STOPS if s.stop_id not in connected_ids]
    assert len(disconnected) >= 1


def test_interchange_pair_is_actually_close_enough_to_be_detected():
    """The two Tripureshwor rows (stop 3, stop 4) must be within the
    interchange proximity threshold, or graph_builder.py will silently
    fail to connect them and no transfer route will ever be found."""
    stop_a = next(s for s in STOPS if s.stop_id == 3)
    stop_b = next(s for s in STOPS if s.stop_id == 4)
    d = haversine_distance(stop_a.lat, stop_a.lng, stop_b.lat, stop_b.lng)
    assert d <= INTERCHANGE_DISTANCE


def test_all_route_stops_reference_a_real_stop_id():
    """Catches typos: a route_stops row pointing at a stop_id that
    doesn't exist in STOPS would crash graph_builder.py with a KeyError."""
    stop_ids = {s.stop_id for s in STOPS}
    for rs in ROUTE_STOPS:
        assert rs.stop_id in stop_ids
```

## backend/app/graph_engine/tests/test_utils.py

```python
"""Tests for utils.py — is the distance calculation numerically correct."""
from app.graph_engine.utils import haversine_distance


def test_distance_between_identical_points_is_zero():
    d = haversine_distance(27.7075, 85.3155, 27.7075, 85.3155)
    assert d == 0


def test_distance_matches_known_real_world_trip():
    """Ratnapark -> Tripureshwor is a known, short real-world distance --
    checked against a plausible range, not an exact hardcoded value,
    since haversine gives straight-line distance, not road distance."""
    d = haversine_distance(27.7075, 85.3155, 27.6953, 85.3130)
    assert 1000 < d < 2000


def test_distance_is_symmetric():
    d1 = haversine_distance(27.7075, 85.3155, 27.6953, 85.3130)
    d2 = haversine_distance(27.6953, 85.3130, 27.7075, 85.3155)
    assert abs(d1 - d2) < 0.001
```

## backend/app/graph_engine/utils.py

```python
"""Minimal helpers: haversine distance in metres."""

import math

from .constants import EARTH_RADIUS


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return float(EARTH_RADIUS * c)
```

## backend/app/main.py

```python
from fastapi import FastAPI

app = FastAPI(
    title="Kathmandu Bus Route Finder API",
    description="Origin-destination bus route search for the Kathmandu Valley.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Routers will be included here as they're built, e.g.:
# from app.api import routes, stops
# app.include_router(routes.router, prefix="/api/route", tags=["route"])
# app.include_router(stops.router, prefix="/api/stops", tags=["stops"])
```

## backend/app/models/__init__.py

```python
from .admin_user import AdminUser
from .base import Base
from .route import Route
from .route_stop import RouteStop
from .stop import Stop

__all__ = [
    "Base",
    "Stop",
    "Route",
    "RouteStop",
    "AdminUser",
]
```

## backend/app/models/admin_user.py

```python
"""
SQLAlchemy ORM model for administrator accounts.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AdminUser(Base):
    """
    Represents an administrator who can access
    protected backend endpoints.
    """

    __tablename__ = "admin_users"

    # ----------------------------------------
    # Primary Key
    # ----------------------------------------
    admin_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # ----------------------------------------
    # Login Credentials
    # ----------------------------------------
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ----------------------------------------
    # Authorization
    # ----------------------------------------
    role: Mapped[str] = mapped_column(
        String(20),
        default="admin",
        nullable=False,
    )

    # ----------------------------------------
    # Metadata
    # ----------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ----------------------------------------
    # Debug Representation
    # ----------------------------------------
    def __repr__(self) -> str:
        return (
            f"AdminUser("
            f"id={self.admin_id}, "
            f"username='{self.username}', "
            f"role='{self.role}')"
        )
```

## backend/app/models/base.py

```python
"""
Base class for all SQLAlchemy ORM models.

Every model in the application (Stop, Route, RouteStop, AdminUser)
inherits from this class so SQLAlchemy can manage them collectively.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
```

## backend/app/models/route.py

```python
"""
SQLAlchemy ORM model for the bus routes table.
"""
from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Route(Base):
    """
    Represents a bus route stored in the database.
    """

    __tablename__ = "routes"

    # ---------------------------------
    # Primary Key
    # ---------------------------------
    route_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # ---------------------------------
    # Route Information
    # ---------------------------------
    route_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ---------------------------------
    # Relationship
    # ---------------------------------
    route_stops: Mapped[list["RouteStop"]] = relationship(
        "RouteStop",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteStop.sequence",
    )

    # ---------------------------------
    # String Representation
    # ---------------------------------
    def __repr__(self) -> str:
        return (
            f"Route("
            f"id={self.route_id}, "
            f"name='{self.route_name}')"
        )
```

## backend/app/models/route_stop.py

```python
"""
SQLAlchemy ORM model representing the association between
bus routes and bus stops.

Each row indicates that a particular stop belongs to a
particular route at a specific position (sequence).
"""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RouteStop(Base):
    """
    Association table connecting routes and stops.

    Example
    -------
    Route A

        Ratnapark
            ↓
        Putalisadak
            ↓
        Baneshwor

    is stored as

        route_id=1 stop_id=5 sequence=1
        route_id=1 stop_id=8 sequence=2
        route_id=1 stop_id=9 sequence=3
    """

    __tablename__ = "route_stops"

    # ---------------------------------------
    # Primary Key
    # ---------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # ---------------------------------------
    # Foreign Keys
    # ---------------------------------------
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.route_id", ondelete="CASCADE"),
        nullable=False,
    )

    stop_id: Mapped[int] = mapped_column(
        ForeignKey("stops.stop_id", ondelete="CASCADE"),
        nullable=False,
    )

    # ---------------------------------------
    # Order of stop inside the route
    # ---------------------------------------
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ---------------------------------------
    # Relationships
    # ---------------------------------------
    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="route_stops",
    )

    stop: Mapped["Stop"] = relationship(
        "Stop",
        back_populates="route_stops",
    )

    # ---------------------------------------
    # Constraints
    # ---------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "route_id",
            "sequence",
            name="uq_route_sequence",
        ),
    )

    # ---------------------------------------
    # Debug Representation
    # ---------------------------------------
    def __repr__(self) -> str:
        return (
            f"RouteStop("
            f"route={self.route_id}, "
            f"stop={self.stop_id}, "
            f"sequence={self.sequence})"
        )
```

## backend/app/models/stop.py

```python
"""
SQLAlchemy ORM model for the bus stops table.
"""

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Stop(Base):
    """
    Represents a bus stop stored in the database.
    """

    __tablename__ = "stops"

    # -----------------------------
    # Primary Key
    # -----------------------------
    stop_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # -----------------------------
    # Stop Information
    # -----------------------------
    stop_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # -----------------------------
    # Relationship
    # -----------------------------
    route_stops = relationship(
        "RouteStop",
        back_populates="stop",
        cascade="all, delete-orphan",
    )

    # -----------------------------
    # Database Indexes
    # -----------------------------
    __table_args__ = (
        Index("idx_stop_location", "latitude", "longitude"),
    )

    # -----------------------------
    # String Representation
    # -----------------------------
    def __repr__(self) -> str:
        return (
            f"Stop("
            f"id={self.stop_id}, "
            f"name='{self.stop_name}')"
        )
```

## backend/migrations/env.py

```python
import os
from logging.config import fileConfig
from app.models.base import Base
from sqlalchemy import engine_from_config, pool
from alembic import context

from dotenv import load_dotenv

# 👇 load .env
load_dotenv()

# this is the Alembic Config object
config = context.config

# 👇 override DB URL from .env
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL is not set in .env")

config.set_main_option("sqlalchemy.url", database_url)

# logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 👇 import your models here
from app.models import Base  # adjust if needed

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## backend/migrations/versions/0001_initial_schema.py

```python
"""Initial schema: stops, routes, route_stops

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-30

"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:

    # PostGIS extension should be created by database administrator:
    # CREATE EXTENSION IF NOT EXISTS postgis;


    # -------------------------
    # Stops table
    # -------------------------
    op.create_table(
        "stops",
        sa.Column(
            "stop_id",
            sa.Integer,
            primary_key=True,
            autoincrement=True
        ),

        sa.Column(
            "name",
            sa.String(150),
            nullable=False
        ),

        sa.Column(
            "name_normalized",
            sa.String(150),
            nullable=False
        ),

        sa.Column(
            "is_interchange",
            sa.Boolean,
            nullable=False,
            server_default=sa.false()
        ),

        sa.Column(
            "geom",
            Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False
            ),
            nullable=False
        ),

        sa.Column(
            "verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.false()
        ),

        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()")
        ),

        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()")
        ),
    )


    # Spatial index for nearby stop search
    op.create_index(
        "idx_stops_geom",
        "stops",
        ["geom"],
        postgresql_using="gist"
    )

    op.create_index(
        "idx_stops_name_normalized",
        "stops",
        ["name_normalized"]
    )


    # -------------------------
    # Routes table
    # -------------------------
    op.create_table(
        "routes",

        sa.Column(
            "route_id",
            sa.Integer,
            primary_key=True,
            autoincrement=True
        ),

        sa.Column(
            "route_number",
            sa.String(20),
            nullable=False
        ),

        sa.Column(
            "route_name",
            sa.String(150),
            nullable=False
        ),

        sa.Column(
            "operator",
            sa.String(100),
            nullable=True
        ),

        sa.Column(
            "tier",
            sa.SmallInteger,
            nullable=True
        ),

        sa.Column(
            "verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.false()
        ),

        sa.Column(
            "source",
            sa.String(50),
            nullable=True
        ),

        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()")
        ),

        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()")
        ),

        sa.CheckConstraint(
            "tier IN (1,2,3)",
            name="ck_routes_tier"
        ),
    )


    op.create_index(
        "idx_routes_tier",
        "routes",
        ["tier"]
    )

    op.create_index(
        "idx_routes_verified",
        "routes",
        ["verified"]
    )


    # -------------------------
    # Route stops mapping table
    # -------------------------
    op.create_table(
        "route_stops",

        sa.Column(
            "route_id",
            sa.Integer,
            sa.ForeignKey(
                "routes.route_id",
                ondelete="CASCADE"
            ),
            nullable=False
        ),

        sa.Column(
            "stop_id",
            sa.Integer,
            sa.ForeignKey(
                "stops.stop_id",
                ondelete="CASCADE"
            ),
            nullable=False
        ),

        sa.Column(
            "sequence_order",
            sa.Integer,
            nullable=False
        ),

        sa.PrimaryKeyConstraint(
            "route_id",
            "sequence_order"
        ),
    )


    op.create_index(
        "idx_route_stops_route_id",
        "route_stops",
        ["route_id"]
    )

    op.create_index(
        "idx_route_stops_stop_id",
        "route_stops",
        ["stop_id"]
    )

    op.create_index(
        "uq_route_stop_position",
        "route_stops",
        [
            "route_id",
            "stop_id",
            "sequence_order"
        ],
        unique=True
    )


def downgrade() -> None:

    op.drop_index(
        "uq_route_stop_position",
        table_name="route_stops"
    )

    op.drop_index(
        "idx_route_stops_stop_id",
        table_name="route_stops"
    )

    op.drop_index(
        "idx_route_stops_route_id",
        table_name="route_stops"
    )

    op.drop_table("route_stops")


    op.drop_index(
        "idx_routes_verified",
        table_name="routes"
    )

    op.drop_index(
        "idx_routes_tier",
        table_name="routes"
    )

    op.drop_table("routes")


    op.drop_index(
        "idx_stops_name_normalized",
        table_name="stops"
    )

    op.drop_index(
        "idx_stops_geom",
        table_name="stops"
    )

    op.drop_table("stops")
```

## backend/readme.md

```markdown
# this will be my folder structure

backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── stops.py
│   │   ├── admin.py
│   │   └── schemas.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── graph_loader.py
│   │   └── schema.sql
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   │
│   ├── graph_engine/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── models.py
│   │   ├── utils.py
│   │   ├── sample_data.py
│   │   ├── graph_builder.py
│   │   ├── route_finder.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_utils.py
│   │       ├── test_graph_builder.py
│   │       ├── test_route_finder.py
│   │       ├── test_sample_data.py
│   │       └── test_integration.py
│   │
│   ├── __init__.py
│   └── main.py
│
├── migrations/
├── tests/
├── .env.example
├── alembic.ini
├── Dockerfile
└── requirements.txt
```

## backend/requirements.txt

```text
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
geoalchemy2==0.15.1
psycopg2-binary==2.9.9
pydantic==2.7.4
pydantic-settings==2.3.3
networkx==3.3
python-dotenv==1.0.1
pytest==8.2.2
httpx==0.27.0
alembic==1.13.2
```

## backend/tests/__init__.py

```python

```

## backend/tests/test_stops.py

```python
"""
Scrum 6: Spatial query accuracy, route continuity, and edge case tests.

Fill these in once app/db/data_access.py (Scrum 5) exists.
"""


def test_placeholder():
    """Replace with real tests once get_nearest_stop / get_route_sequences exist."""
    assert True


# Planned test cases (Scrum 6):
# - test_nearest_stop_returns_closest_within_radius()
# - test_nearest_stop_no_match_returns_none()
# - test_route_sequence_is_continuous_and_ordered()
# - test_invalid_coordinates_rejected()
# - test_duplicate_stop_within_30m_flagged()
```

## data/README.md

```markdown
# Data

Owner: Dipesh S Saud — Scrum tasks 1-8 (schema, ingestion, cleaning, spatial queries, data access layer).

```
data/
├── raw/          Original exports (2013 Yatayat OSM export, Overpass Turbo pulls, DOTM records)
├── processed/    Cleaned, deduplicated, validated CSV/JSON ready for DB import
└── scripts/      ETL scripts: dedup (~30m threshold), coordinate validation, name normalization
```

## Pipeline order

1. `scripts/import_raw.py` — load raw OSM/DOTM exports
2. `scripts/dedupe_stops.py` — merge stops within ~30m (Scrum 3)
3. `scripts/validate_coords.py` — reject out-of-bounds coordinates (Scrum 3)
4. `scripts/normalize_names.py` — lowercase/trim stop & route names for matching
5. `scripts/load_to_db.py` — insert into `stops`, `routes`, `route_stops` (uses `backend/app/db/schema.sql`)

## Current dataset status

- 57 verified routes, 206 stops (Tier 1 + Tier 2 complete; Tier 3 in progress — 13 routes pending field verification)
```

## docker-compose.yml

```yaml
version: "3.9"

services:
  db:
    image: postgis/postgis:15-3.4
    container_name: ktm_bus_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ktm_bus
      POSTGRES_PASSWORD: ktm_bus_dev
      POSTGRES_DB: ktm_bus_route_finder
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    # Schema is created via Alembic migrations (backend/migrations), not an init script.
    # Run `alembic upgrade head` from backend/ after the db container is up.

  backend:
    build: ./backend
    container_name: ktm_bus_backend
    restart: unless-stopped
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://ktm_bus:ktm_bus_dev@db:5432/ktm_bus_route_finder
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

volumes:
  pgdata:
```

## docs/README.md

```markdown
# Docs

Put here:
- `minor_project_proposal.pdf` — the approved project proposal
- Gantt chart / time schedule exports
- Defense/viva Q&A, presentation decks
- Architecture diagrams (Figure 5.2.1 etc.)
```

## frontend/README.md

```markdown
# Frontend (Next.js 14 + TypeScript + Leaflet.js)

Not yet scaffolded. To initialize:

```bash
cd frontend
npx create-next-app@14 . --typescript --tailwind --app
npm install leaflet react-leaflet
```

Owner: Dinesh Bhatta — see Scrum tasks 6-7 in the backlog.
```

## requirements.txt

```text
��a s t t o k e n s = = 3 . 0 . 2 
 
 c o l o r a m a = = 0 . 4 . 6 
 
 c o m m = = 0 . 2 . 3 
 
 d e b u g p y = = 1 . 8 . 2 1 
 
 d e c o r a t o r = = 5 . 3 . 1 
 
 e x e c u t i n g = = 2 . 2 . 1 
 
 i n i c o n f i g = = 2 . 3 . 0 
 
 i p y k e r n e l = = 7 . 3 . 0 
 
 i p y t h o n = = 9 . 1 5 . 0 
 
 i p y t h o n _ p y g m e n t s _ l e x e r s = = 1 . 1 . 1 
 
 j e d i = = 0 . 2 0 . 0 
 
 j u p y t e r _ c l i e n t = = 8 . 9 . 1 
 
 j u p y t e r _ c o r e = = 5 . 9 . 1 
 
 m a t p l o t l i b - i n l i n e = = 0 . 2 . 2 
 
 n e s t - a s y n c i o 2 = = 1 . 7 . 2 
 
 n e t w o r k x = = 3 . 6 . 1 
 
 p a c k a g i n g = = 2 6 . 2 
 
 p a r s o = = 0 . 8 . 7 
 
 p l a t f o r m d i r s = = 4 . 1 1 . 0 
 
 p l u g g y = = 1 . 6 . 0 
 
 p r o m p t _ t o o l k i t = = 3 . 0 . 5 3 
 
 p s u t i l = = 7 . 2 . 2 
 
 p u r e _ e v a l = = 0 . 2 . 3 
 
 P y g m e n t s = = 2 . 2 0 . 0 
 
 p y t e s t = = 9 . 1 . 1 
 
 p y t h o n - d a t e u t i l = = 2 . 9 . 0 . p o s t 0 
 
 p y z m q = = 2 7 . 1 . 0 
 
 s i x = = 1 . 1 7 . 0 
 
 s t a c k - d a t a = = 0 . 6 . 3 
 
 t o r n a d o = = 6 . 5 . 7 
 
 t r a i t l e t s = = 5 . 1 5 . 1 
 
 t y p i n g _ e x t e n s i o n s = = 4 . 1 6 . 0 
 
 w c w i d t h = = 0 . 8 . 2 
 
 
```
