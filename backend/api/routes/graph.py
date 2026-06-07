from fastapi import APIRouter
from backend.api.schemas import GraphResponse
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=GraphResponse)
async def get_graph():
    """Return the full transmission graph with nodes and edges."""
    # TODO: Replace with BigQuery graph query
    return GraphResponse(nodes=[], edges=[], regime_tag="AI_CAPEX_EXPANSION", computed_at=datetime.utcnow())
