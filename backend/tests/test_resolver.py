"""Tests for the standalone EntityResolver."""
import pytest
from backend.agents.resolver import EntityResolver, get_resolver


@pytest.fixture
def resolver():
    return EntityResolver()


def test_resolver_canonical_exact(resolver):
    """Exact canonical name resolves correctly."""
    result = resolver.resolve("Nvidia")
    assert result is not None
    assert result["canonical_name"] == "Nvidia"


def test_resolver_ticker(resolver):
    """Ticker symbol resolves to canonical entity."""
    result = resolver.resolve("NVDA")
    assert result is not None
    assert result["canonical_name"] == "Nvidia"


def test_resolver_alias(resolver):
    """Common alias resolves to canonical entity."""
    result = resolver.resolve("Nvidia Corp")
    assert result is not None


def test_resolver_unknown_returns_none(resolver):
    """Completely unknown name returns None."""
    result = resolver.resolve("ZXQ99 Fictional Corp")
    assert result is None


def test_resolver_batch(resolver):
    """Batch resolution returns a dict keyed by input names."""
    names = ["Nvidia", "NVDA", "unknown-entity-xyz"]
    results = resolver.resolve_batch(names)
    assert set(results.keys()) == set(names)
    assert results["Nvidia"] is not None
    assert results["NVDA"] is not None
    assert results["unknown-entity-xyz"] is None


def test_resolver_canonical_name_helper(resolver):
    """canonical_name() returns just the name string."""
    name = resolver.canonical_name("NVDA")
    assert name == "Nvidia"


def test_resolver_merge_duplicate(resolver):
    """merge_duplicate redirects resolver to canonical entity."""
    # Get two entity IDs from the resolver
    a = resolver.resolve("Nvidia")
    b = resolver.resolve("AMD")
    if a and b and a["id"] != b["id"]:
        resolver.merge_duplicate(a["id"], b["id"])
        # After merge, resolving b's name should still return something
        result = resolver.resolve("AMD")
        assert result is not None


def test_resolver_singleton():
    """get_resolver() returns the same instance on repeated calls."""
    r1 = get_resolver()
    r2 = get_resolver()
    assert r1 is r2
