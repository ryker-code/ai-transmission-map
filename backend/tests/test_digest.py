"""Tests for weekly digest generator."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.tests.conftest import AUTH_HEADERS

client = TestClient(app)


def test_generate_weekly_digest_returns_all_keys():
    from backend.tools.digest_generator import generate_weekly_digest
    data = generate_weekly_digest()
    required_keys = [
        "week_ending", "dominant_regime", "regime_changed",
        "top_score_movers", "new_evidence_count", "new_claims_accepted",
        "top_bottleneck", "falsification_alerts", "house_view_summary", "analyst_calls",
    ]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"


def test_generate_weekly_digest_top_bottleneck_structure():
    from backend.tools.digest_generator import generate_weekly_digest
    data = generate_weekly_digest()
    tb = data["top_bottleneck"]
    assert "entity" in tb
    assert "score" in tb
    assert "key_driver" in tb


def test_digest_endpoint_returns_200():
    resp = client.post("/digest/generate", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "digest_text" in body
    assert "generated_at" in body
    assert "data" in body
    assert len(body["digest_text"]) > 100


def test_digest_regime_is_valid():
    from backend.tools.digest_generator import generate_weekly_digest
    data = generate_weekly_digest()
    valid_regimes = {
        "AI_CAPEX_EXPANSION", "SUPPLY_CHAIN_STRESS", "GRID_BOTTLENECK",
        "POWER_PRICE_SPREAD", "REGULATORY",
    }
    assert data["dominant_regime"] in valid_regimes
