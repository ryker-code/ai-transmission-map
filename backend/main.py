import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import evidence, entities, graph, bottlenecks, thesis, memo, house_view

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Transmission Map API", version="0.1.0")

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

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

@app.on_event("startup")
async def startup():
    logger.info("AITM Backend starting...")
