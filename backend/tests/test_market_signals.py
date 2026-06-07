"""Tests for MarketSignals stub and /market/signals endpoint."""
import pytest
from backend.tools.market_signals import MarketSignals


@pytest.fixture
def client():
    from backend.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_market_confirmation_score_with_ticker():
    ms = MarketSignals()
    score = ms.market_confirmation_score("nvda-id", "nvda")
    assert 0.0 <= score <= 1.0
    score_strong = ms.market_confirmation_score("", "nvda")
    score_neutral = ms.market_confirmation_score("", "etn")
    assert score_strong > score_neutral, "Strong bull should score higher than neutral"


def test_momentum_signal_returns_valid_label():
    ms = MarketSignals()
    valid = {"strong_bull", "bull", "neutral", "bear", "strong_bear"}
    assert ms.get_momentum_signal("nvda") in valid
    assert ms.get_momentum_signal("unknown_ticker") in valid


def test_market_signals_endpoint(client):
    r = client.get("/market/signals")
    assert r.status_code == 200
    data = r.json()
    assert "signals" in data
    assert isinstance(data["signals"], list)
    assert len(data["signals"]) > 0
    assert data["is_live"] is False
    first = data["signals"][0]
    assert "ticker" in first
    assert "rel_perf_30d" in first
    assert "momentum" in first
    assert "vol_percentile" in first
    assert "market_confirmation_score" in first
