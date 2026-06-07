from fastapi import APIRouter
from backend.api.schemas import EntityCreate, EntityResponse
from typing import List
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/", response_model=List[EntityResponse])
async def list_entities():
    """Return all entities in the transmission graph."""
    # TODO: Replace with BigQuery query
    return []

@router.post("/", response_model=EntityResponse)
async def create_entity(payload: EntityCreate):
    """Create a new entity node in the graph."""
    return EntityResponse(**payload.model_dump(), id=str(uuid.uuid4()), updated_at=datetime.utcnow())
