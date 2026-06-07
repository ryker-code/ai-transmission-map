"""Tests for SimpleCache: get/set, TTL expiry, prefix invalidation."""
import time
import pytest
from backend.db.cache import SimpleCache


def test_cache_set_and_get():
    cache = SimpleCache()
    cache.set("key1", {"value": 42}, ttl_seconds=60)
    result = cache.get("key1")
    assert result == {"value": 42}


def test_cache_ttl_expiry():
    cache = SimpleCache()
    cache.set("expiring", "hello", ttl_seconds=0)
    # TTL=0 should expire immediately (expires_at = monotonic + 0)
    time.sleep(0.01)
    result = cache.get("expiring")
    assert result is None


def test_cache_invalidate_prefix():
    cache = SimpleCache()
    cache.set("bottlenecks:all", [1, 2, 3], ttl_seconds=60)
    cache.set("bottlenecks:filter", [1], ttl_seconds=60)
    cache.set("graph:all", {"nodes": []}, ttl_seconds=60)

    removed = cache.invalidate_prefix("bottlenecks:")
    assert removed == 2
    assert cache.get("bottlenecks:all") is None
    assert cache.get("bottlenecks:filter") is None
    assert cache.get("graph:all") is not None  # untouched

    stats = cache.stats()
    assert stats["cached_keys"] == 1
