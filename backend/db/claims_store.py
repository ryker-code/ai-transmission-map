"""
In-memory store for runtime pipeline-extracted claims.
Scorer reads from this store alongside seed data.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_claims: list[dict] = []


def add(claims: list[dict]) -> None:
    """Append accepted claims extracted by the pipeline."""
    _claims.extend(claims)
    logger.debug(f"claims_store: +{len(claims)} claims (total={len(_claims)})")


def all_claims() -> list[dict]:
    return list(_claims)


def claims_for_entity(entity_name: str) -> list[dict]:
    return [c for c in _claims if c.get("subject") == entity_name or c.get("object") == entity_name]
