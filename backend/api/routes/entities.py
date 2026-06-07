import json
import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Query
from backend.api.schemas import EntityCreate, EntityResponse
from typing import List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

_ENTITIES_PATH = Path("backend/db/seed_data/entities.json")


@router.get("/", response_model=List[EntityResponse])
async def list_entities(
    sector: str = Query(None, description="Filter by sector"),
    entity_type: str = Query(None, description="Filter by entity_type"),
    limit: int = Query(100, ge=1, le=500),
):
    """Return entities from the transmission graph (seed data + any runtime additions)."""
    if not _ENTITIES_PATH.exists():
        return []
    try:
        entities = json.loads(_ENTITIES_PATH.read_text())
        if sector:
            entities = [e for e in entities if e.get("sector") == sector]
        if entity_type:
            entities = [e for e in entities if e.get("entity_type") == entity_type]
        entities = entities[:limit]
        return [
            EntityResponse(
                id=e["id"],
                canonical_name=e["canonical_name"],
                aliases=e.get("aliases", []),
                entity_type=e["entity_type"],
                ticker=e.get("ticker"),
                sector=e.get("sector"),
                sub_sector=e.get("sub_sector"),
                metadata=e.get("metadata"),
                updated_at=datetime.now(timezone.utc),
            )
            for e in entities
        ]
    except Exception as ex:
        logger.error(f"list_entities failed: {ex}")
        return []


@router.post("/", response_model=EntityResponse)
async def create_entity(payload: EntityCreate):
    """Create a new entity node in the graph."""
    return EntityResponse(
        **payload.model_dump(),
        id=str(uuid.uuid4()),
        updated_at=datetime.now(timezone.utc),
    )
