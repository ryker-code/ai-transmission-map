"""Tests for the 5-component weighted bottleneck scorer."""
import pytest
from backend.agents.scorer import compute_bottleneck_scores


def test_scorer_returns_ranked_list():
    """Scorer returns a non-empty ranked list from seed data."""
    results = compute_bottleneck_scores()
    assert len(results) > 0, "Scorer should return at least one entry from seed data"
    # Verify ranking is sequential starting at 1
    for i, entry in enumerate(results):
        assert entry.rank == i + 1
    # Scores descending
    scores = [e.score for e in results]
    assert scores == sorted(scores, reverse=True)


def test_scorer_score_range():
    """All scores are in 0-100 range."""
    results = compute_bottleneck_scores()
    for entry in results:
        assert 0 <= entry.score <= 100, f"Score out of range: {entry.entity_name}={entry.score}"


def test_scorer_has_all_components():
    """Every entry exposes all 5 scoring components."""
    results = compute_bottleneck_scores()
    required = {"evidence_intensity", "recency_score", "cross_source_agreement",
                "market_confirmation", "house_view_weight"}
    for entry in results[:5]:
        missing = required - set(entry.components.keys())
        assert not missing, f"{entry.entity_name} missing components: {missing}"


def test_scorer_entity_ids_filter():
    """Passing entity_ids limits results to those entities."""
    all_results = compute_bottleneck_scores()
    if not all_results:
        pytest.skip("No scored entities in seed data")
    target_id = all_results[0].entity_id
    filtered = compute_bottleneck_scores(entity_ids=[target_id])
    assert len(filtered) == 1
    assert filtered[0].entity_id == target_id
