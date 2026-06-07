import logging
from fastapi import APIRouter, Query
from backend.api.schemas import BottlenecksResponse
from backend.db.cache import get_cache
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()
_cache = get_cache()


@router.get("/", response_model=BottlenecksResponse)
async def get_bottlenecks(
    limit: int = Query(20, ge=1, le=100),
    regime: str = Query(None, description="Filter by regime tag"),
):
    """
    Return ranked bottleneck nodes by 5-component composite score (normalized 0-100).
    Weights: evidence_intensity×0.30, recency×0.20, cross_source×0.25,
             market_confirmation×0.15, house_view_weight×0.10.
    Analyst house view conviction adjustments are applied before final ranking.
    """
    cache_key = f"bottlenecks:{regime or 'all'}:{limit}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        from backend.agents.scorer import compute_bottleneck_scores
        from backend.agents.house_view import apply_house_view

        bottlenecks = compute_bottleneck_scores()
        bottlenecks, pinned = apply_house_view(bottlenecks)

        if regime:
            bottlenecks = [b for b in bottlenecks if b.regime_tag == regime]

        bottlenecks = bottlenecks[:limit]
        for i, b in enumerate(bottlenecks):
            b.rank = i + 1

        result = BottlenecksResponse(
            bottlenecks=bottlenecks,
            total=len(bottlenecks),
            computed_at=datetime.now(timezone.utc),
        )
        _cache.set(cache_key, result, ttl_seconds=30)
        return result
    except Exception as e:
        logger.error(f"Bottlenecks scorer failed: {e}")
        return BottlenecksResponse(bottlenecks=[], total=0, computed_at=datetime.now(timezone.utc))
