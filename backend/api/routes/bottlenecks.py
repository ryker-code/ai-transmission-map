from fastapi import APIRouter, Query
from backend.api.schemas import BottlenecksResponse
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=BottlenecksResponse)
async def get_bottlenecks(limit: int = Query(20, ge=1, le=100)):
    """Return ranked bottleneck nodes by score."""
    # TODO: Replace with real scorer query
    return BottlenecksResponse(bottlenecks=[], total=0, computed_at=datetime.utcnow())
