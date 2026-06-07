import logging
from fastapi import APIRouter
from backend.api.schemas import HouseViewUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put("/", response_model=dict)
async def update_house_view(payload: HouseViewUpdate):
    """
    Update analyst conviction weight and annotations for an entity.
    Weight override is applied immediately to subsequent bottleneck scoring.
    """
    from backend.db.house_view_store import put as store_view
    store_view(payload.entity_id, {
        "weight_override": payload.weight_override,
        "conviction": payload.conviction,
        "analyst_note": payload.analyst_note,
        "pinned_thesis": payload.pinned_thesis,
    })
    logger.info(f"House view updated: entity={payload.entity_id} weight={payload.weight_override} conviction={payload.conviction}")
    return {"status": "updated", "entity_id": payload.entity_id, "weight_override": payload.weight_override}


@router.get("/", response_model=dict)
async def list_house_views():
    """Return all active analyst house view overrides."""
    from backend.db.house_view_store import all_entries
    return {"house_views": all_entries(), "total": len(all_entries())}
