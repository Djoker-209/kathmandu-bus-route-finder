import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, admin_auth, routes, routing, stops
from app.core.security import require_admin_key
from app.db.session import SessionLocal
from app.routing import graph_builder

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the graph cache at startup instead of on the first request.
    db = SessionLocal()
    try:
        graph = graph_builder.get_cached_graph(db)
        logger.info(
            "Routing graph built: %d stops, %d edges",
            graph.number_of_nodes(),
            graph.number_of_edges(),
        )
    except Exception:
        logger.exception("Failed to build routing graph at startup")
    finally:
        db.close()

    yield

app = FastAPI(
    title="Kathmandu Bus Route Finder API",
    description="Origin-destination bus route search for the Kathmandu Valley.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/admin/rebuild-graph", dependencies=[Depends(require_admin_key)])
def rebuild_graph():
    db = SessionLocal()
    try:
        graph = graph_builder.get_cached_graph(db, refresh=True)
        return {"status": "ok", "stops": graph.number_of_nodes(), "edges": graph.number_of_edges()}
    finally:
        db.close()


app.include_router(stops.router)
app.include_router(routes.router)
app.include_router(routing.router)
app.include_router(admin.router)
app.include_router(admin_auth.router)