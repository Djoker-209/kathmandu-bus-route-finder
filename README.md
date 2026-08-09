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
| Database   | PostgreSQL 16.14 + PostGIS                |
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
