"""Watchlist routes: GET/POST/DELETE /watchlist/{entity_id}."""
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.api.schemas import WatchlistEntry, WatchlistResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_ENTITIES_PATH = Path(__file__).parent.parent.parent / "db/seed_data/entities.json"


def _entity_map() -> dict:
    if not _ENTITIES_PATH.exists():
        return {}
    entities = json.loads(_ENTITIES_PATH.read_text())
    return {e["id"]: e for e in entities}


def _score_for(entity_id: str) -> float | None:
    try:
        from backend.agents.scorer import compute_bottleneck_scores
        scores = compute_bottleneck_scores(entity_ids=[entity_id])
        return scores[0].score if scores else None
    except Exception:
        return None


@router.get("/", response_model=WatchlistResponse)
async def get_watchlist():
    """Return all watched entities with current bottleneck scores and momentum."""
    from backend.db.watchlist_store import list_watched
    from backend.tools.market_signals import get_signals

    watched_ids = list_watched()
    entity_map = _entity_map()
    signals = get_signals()
    entries: list[WatchlistEntry] = []

    # Build ticker → signal dict for O(1) lookup
    all_sigs = {s["ticker"].lower(): s for s in signals.get_all_signals() if s.get("ticker")}

    for eid in watched_ids:
        entity = entity_map.get(eid)
        if not entity:
            continue
        score = _score_for(eid)
        ticker = entity.get("ticker")
        momentum = "neutral"
        if ticker:
            sig = all_sigs.get(ticker.lower())
            if sig:
                momentum = sig.get("momentum", "neutral")
        entries.append(WatchlistEntry(
            entity_id=eid,
            name=entity["canonical_name"],
            ticker=ticker,
            bottleneck_score=score,
            score_delta_24h=0.0,
            momentum=momentum,
            is_watched=True,
        ))

    return WatchlistResponse(entries=entries, total=len(entries))


@router.post("/{entity_id}", response_model=dict)
async def add_to_watchlist(entity_id: str):
    """Add an entity to the watchlist."""
    from backend.db.watchlist_store import add
    entity_map = _entity_map()
    if entity_id not in entity_map:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    add(entity_id)
    logger.info(f"Watchlist: added {entity_id}")
    return {"status": "added", "entity_id": entity_id}


@router.delete("/{entity_id}", response_model=dict)
async def remove_from_watchlist(entity_id: str):
    """Remove an entity from the watchlist."""
    from backend.db.watchlist_store import remove, is_watched
    if not is_watched(entity_id):
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not in watchlist")
    remove(entity_id)
    logger.info(f"Watchlist: removed {entity_id}")
    return {"status": "removed", "entity_id": entity_id}
