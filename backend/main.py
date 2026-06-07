import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import evidence, entities, graph, bottlenecks, thesis, memo, house_view, regime, claims, models, market

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AITM Backend starting...")
    yield
    logger.info("AITM Backend shutting down.")


app = FastAPI(title="AI Transmission Map API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
app.include_router(entities.router, prefix="/entities", tags=["entities"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(bottlenecks.router, prefix="/bottlenecks", tags=["bottlenecks"])
app.include_router(thesis.router, prefix="/thesis", tags=["thesis"])
app.include_router(memo.router, prefix="/memo", tags=["memo"])
app.include_router(house_view.router, prefix="/house-view", tags=["house-view"])
app.include_router(regime.router, prefix="/regime", tags=["regime"])
app.include_router(claims.router, prefix="/claims", tags=["claims"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(market.router, prefix="/market", tags=["market"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/cache/stats")
async def cache_stats():
    """Return cache hit/miss stats (dev endpoint)."""
    from backend.db.cache import get_cache
    return get_cache().stats()
