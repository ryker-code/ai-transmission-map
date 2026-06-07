"""
Simple in-process TTL cache for slow/expensive API endpoints.
No external dependencies — just a dict + timestamp per key.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (value, time.monotonic() + ttl_seconds)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all keys starting with prefix. Returns count removed."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        logger.debug(f"cache: invalidated {len(keys)} keys with prefix '{prefix}'")
        return len(keys)

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total else 0.0,
            "cached_keys": len(self._store),
        }


_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Return module-level singleton cache."""
    return _cache
