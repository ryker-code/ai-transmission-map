"""Tests for ModelRouter: routing, logging, stats, and /models/status endpoint."""
from pathlib import Path
from unittest.mock import patch

import pytest
from backend.tools.model_router import ModelRouter


@pytest.fixture
def client():
    from backend.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_route_returns_correct_model():
    router = ModelRouter()
    assert router.route("entity_extraction") == "gemini-2.5-flash"
    assert router.route("causal_reasoning") == "gemma-4-31b-it"
    assert router.route("voice_transcription") == "gemini-3.1-flash-lite"


def test_route_unknown_defaults_to_gemini():
    router = ModelRouter()
    result = router.route("totally_unknown_task")
    assert result == "gemini-2.5-flash"


def test_log_call_and_get_stats(tmp_path):
    router = ModelRouter()
    log_path = tmp_path / "model_call_log.jsonl"
    with patch("backend.tools.model_router._LOG_PATH", log_path):
        router.log_call("entity_extraction", "gemini-2.0-flash", 100, 50, 120, True)
        router.log_call("causal_reasoning", "gemma-4-31b-it", 200, 150, 800, True)
        router.log_call("causal_reasoning", "gemma-4-31b-it", 200, 0, 500, False)
        stats = router.get_stats()

    assert "gemini-2.0-flash" in stats
    assert stats["gemini-2.0-flash"]["call_count"] == 1
    assert stats["gemini-2.0-flash"]["success_rate"] == 1.0

    assert "gemma-4-31b-it" in stats
    assert stats["gemma-4-31b-it"]["call_count"] == 2
    assert stats["gemma-4-31b-it"]["success_rate"] == 0.5
    assert stats["gemma-4-31b-it"]["avg_latency_ms"] == 650


def test_models_status_endpoint(client):
    r = client.get("/models/status")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    names = [m["name"] for m in data["models"]]
    assert any("gemini" in n or "gemma" in n for n in names)
