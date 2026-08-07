import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import admin, routes, routing, stops
from app.db.session import SessionLocal
from app.routing import graph_builder

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(stops.router)
app.include_router(routes.router)
app.include_router(routing.router)
app.include_router(admin.router)