from fastapi import APIRouter
from backend.api.schemas import HouseViewUpdate

router = APIRouter()

@router.put("/", response_model=dict)
async def update_house_view(payload: HouseViewUpdate):
    """Update analyst conviction weight and annotations for an entity."""
    # TODO: Replace with BigQuery upsert
    return {"status": "updated", "entity_id": payload.entity_id}
