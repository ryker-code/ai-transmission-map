"""
Shared in-memory run cache for thesis and memo routes.
Keyed by run_id (UUID string). In production, backed by BigQuery aitm.thesis_runs.
"""
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_cache: dict[str, dict] = {}


def put(run_id: str, data: dict) -> None:
    """Store a thesis run result."""
    _cache[run_id] = data
    logger.debug(f"run_cache: stored run_id={run_id}")


def get(run_id: str) -> Optional[dict]:
    """Retrieve a thesis run result, or None if not found."""
    return _cache.get(run_id)
