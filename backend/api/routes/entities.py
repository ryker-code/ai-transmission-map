import json
import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Query
from backend.api.schemas import EntityCreate, EntityDetailResponse, EntityResponse, ClaimSummary
from typing import List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

_ENTITIES_PATH = Path(__file__).parent.parent.parent / "db/seed_data/entities.json"
_CHAINS_PATH = Path(__file__).parent.parent.parent / "db/seed_data/transmission_chains.json"


def _load_seed():
    entities = json.loads(_ENTITIES_PATH.read_text()) if _ENTITIES_PATH.exists() else []
    chains = json.loads(_CHAINS_PATH.read_text()) if _CHAINS_PATH.exists() else []
    return entities, chains


@router.get("/", response_model=List[EntityResponse])
async def list_entities(
    sector: str = Query(None),
    entity_type: str = Query(None),
    search: str = Query(None, description="Substring search on canonical_name or aliases"),
    limit: int = Query(100, ge=1, le=500),
):
    """Return entities from the transmission graph with optional sector, type, and search filters."""
    if not _ENTITIES_PATH.exists():
        return []
    try:
        entities, _ = _load_seed()
        if sector:
            entities = [e for e in entities if e.get("sector") == sector]
        if entity_type:
            entities = [e for e in entities if e.get("entity_type") == entity_type]
        if search:
            q = search.lower()
            entities = [
                e for e in entities
                if q in e["canonical_name"].lower()
                or any(q in a.lower() for a in e.get("aliases", []))
                or (e.get("ticker") and q in e["ticker"].lower())
            ]
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


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity_detail(entity_id: str):
    """
    Return full entity detail: metadata, bottleneck score, inbound/outbound claims,
    house view status, and top 3 related entities.
    """
    entities, chains = _load_seed()

    entity = next((e for e in entities if e["id"] == entity_id), None)
    if entity is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    name = entity["canonical_name"]

    # Build claim summaries
    def chain_to_summary(c: dict, idx: int) -> ClaimSummary:
        return ClaimSummary(
            claim_id=c.get("id", f"seed-{idx}"),
            subject=c["subject"],
            predicate=c["predicate"],
            object=c["object"],
            direction=c["direction"],
            confidence=float(c["confidence"]),
            horizon=c["horizon"],
            regime_tag=c.get("regime_tag", "AI_CAPEX_EXPANSION"),
            analyst_note=c.get("analyst_note"),
        )

    outbound = [chain_to_summary(c, i) for i, c in enumerate(chains) if c["subject"] == name]
    inbound = [chain_to_summary(c, i) for i, c in enumerate(chains) if c["object"] == name]

    # Bottleneck score from scorer
    bottleneck_score = None
    bottleneck_components = None
    try:
        from backend.agents.scorer import compute_bottleneck_scores
        scores = compute_bottleneck_scores(entity_ids=[entity_id])
        if scores:
            bottleneck_score = scores[0].score
            bottleneck_components = scores[0].components
    except Exception as e:
        logger.warning(f"Scorer failed for entity detail: {e}")

    # House view
    house_view_data = None
    try:
        from backend.db.house_view_store import get as get_hv
        hv = get_hv(entity_id)
        if hv:
            house_view_data = hv
    except Exception:
        pass

    # Related entities: entities that appear alongside this one in claims
    related_names: dict = {}
    for c in outbound:
        related_names[c.object] = related_names.get(c.object, 0) + 1
    for c in inbound:
        related_names[c.subject] = related_names.get(c.subject, 0) + 1
    related_names.pop(name, None)
    top_related_names = sorted(related_names, key=related_names.get, reverse=True)[:3]
    entity_index = {e["canonical_name"]: e for e in entities}
    related_entities = [
        {"id": entity_index[n]["id"], "canonical_name": n,
         "entity_type": entity_index[n]["entity_type"],
         "claim_count": related_names[n]}
        for n in top_related_names if n in entity_index
    ]

    return EntityDetailResponse(
        id=entity["id"],
        canonical_name=name,
        entity_type=entity["entity_type"],
        ticker=entity.get("ticker"),
        sector=entity.get("sector"),
        sub_sector=entity.get("sub_sector"),
        aliases=entity.get("aliases", []),
        bottleneck_score=bottleneck_score,
        bottleneck_components=bottleneck_components,
        outbound_claims=outbound,
        inbound_claims=inbound,
        house_view=house_view_data,
        related_entities=related_entities,
    )


@router.post("/", response_model=EntityResponse)
async def create_entity(payload: EntityCreate):
    """Create a new entity node in the graph."""
    return EntityResponse(
        **payload.model_dump(),
        id=str(uuid.uuid4()),
        updated_at=datetime.now(timezone.utc),
    )
