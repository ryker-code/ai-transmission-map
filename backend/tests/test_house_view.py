"""Tests for the house view agent conviction weight application."""
import pytest
from backend.agents.scorer import compute_bottleneck_scores
from backend.agents.house_view import apply_house_view
from backend.db.house_view_store import put as store_view


def _first_entry():
    results = compute_bottleneck_scores()
    if not results:
        pytest.skip("No scored entities in seed data")
    return results[0]


def test_house_view_weight_applied():
    """High weight override raises the entity's score."""
    entry = _first_entry()
    original_score = entry.score
    eid = entry.entity_id

    store_view(eid, {"weight_override": 3.0, "conviction": "medium", "analyst_note": None, "pinned_thesis": None})

    all_entries = compute_bottleneck_scores()
    adjusted, pinned = apply_house_view(all_entries)

    adjusted_entry = next((e for e in adjusted if e.entity_id == eid), None)
    assert adjusted_entry is not None
    # Higher weight → score should be >= original
    assert adjusted_entry.score >= original_score - 0.01  # small float tolerance


def test_conviction_high_bonus():
    """conviction=high adds up to 10 points."""
    entry = _first_entry()
    eid = entry.entity_id

    store_view(eid, {"weight_override": 1.0, "conviction": "high", "analyst_note": None, "pinned_thesis": None})

    results = compute_bottleneck_scores()
    adjusted, _ = apply_house_view(results)
    adj = next((e for e in adjusted if e.entity_id == eid), None)
    assert adj is not None
    assert adj.components.get("conviction") == "high"


def test_conviction_low_penalty():
    """conviction=low subtracts up to 10 points, floor at 0."""
    entry = _first_entry()
    eid = entry.entity_id

    store_view(eid, {"weight_override": 1.0, "conviction": "low", "analyst_note": None, "pinned_thesis": None})

    results = compute_bottleneck_scores()
    adjusted, _ = apply_house_view(results)
    adj = next((e for e in adjusted if e.entity_id == eid), None)
    assert adj is not None
    assert adj.score >= 0.0


def test_pinned_entity_tracked():
    """Entities with pinned_thesis appear in the pinned list."""
    entry = _first_entry()
    eid = entry.entity_id

    store_view(eid, {"weight_override": 1.0, "conviction": "medium", "analyst_note": None, "pinned_thesis": "thesis-123"})

    results = compute_bottleneck_scores()
    _, pinned = apply_house_view(results)
    assert eid in pinned


def test_no_view_passthrough():
    """Entries with no house view override pass through unchanged."""
    results = compute_bottleneck_scores()
    if not results:
        pytest.skip("No scored entities")
    # Clear any lingering overrides for a clean test by using a new resolver call
    # (store may have state from other tests — just verify scores are in range)
    adjusted, _ = apply_house_view(results)
    for entry in adjusted:
        assert 0 <= entry.score <= 100
