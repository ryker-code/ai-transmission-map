"""
In-memory store for analyst house view overrides (conviction, weight, pinned thesis).
Applied by the scorer to adjust bottleneck scores. In production, backed by BigQuery aitm.house_view.
"""
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# {entity_id: {weight_override, conviction, analyst_note, pinned_thesis}}
_store: dict[str, dict] = {}


def put(entity_id: str, data: dict) -> None:
    _store[entity_id] = data
    logger.debug(f"house_view_store: updated entity_id={entity_id}")


def get(entity_id: str) -> Optional[dict]:
    return _store.get(entity_id)


def get_weight(entity_id: str, default: float = 1.0) -> float:
    entry = _store.get(entity_id)
    if entry is None:
        return default
    return float(entry.get("weight_override", default))


def all_entries() -> dict[str, dict]:
    return dict(_store)
