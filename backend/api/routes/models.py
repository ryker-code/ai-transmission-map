"""Models status endpoint: returns per-model call stats from the call log."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.api.schemas import ModelStatusEntry, ModelStatusResponse
from backend.tools.model_router import get_router
from backend.db.cache import get_cache

logger = logging.getLogger(__name__)
router = APIRouter()
_cache = get_cache()

ROUTING_TABLE = get_router().ROUTING_TABLE


@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status():
    """Return per-model call counts, avg latency, and success rate from the call log."""
    cached = _cache.get("models:status")
    if cached is not None:
        return cached
    try:
        stats = get_router().get_stats()
        entries = []
        seen_models = set()

        for model, data in stats.items():
            seen_models.add(model)
            task_types = [t for t, m in ROUTING_TABLE.items() if m == model]
            entries.append(ModelStatusEntry(
                name=model,
                task_types=task_types or data.get("task_types", []),
                call_count=data["call_count"],
                avg_latency_ms=data["avg_latency_ms"],
                success_rate=data["success_rate"],
            ))

        # Include models with no calls yet
        for task_type, model in ROUTING_TABLE.items():
            if model not in seen_models:
                seen_models.add(model)
                task_types = [t for t, m in ROUTING_TABLE.items() if m == model]
                entries.append(ModelStatusEntry(
                    name=model,
                    task_types=task_types,
                    call_count=0,
                    avg_latency_ms=0,
                    success_rate=1.0,
                ))

        result = ModelStatusResponse(
            models=entries,
            is_live=True,
            last_updated=datetime.now(timezone.utc),
        )
        _cache.set("models:status", result, ttl_seconds=10)
        return result
    except Exception as e:
        logger.error(f"model status failed: {e}")
        return ModelStatusResponse(models=[], is_live=False, last_updated=datetime.now(timezone.utc))
