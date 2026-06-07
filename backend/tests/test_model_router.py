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
    assert router.route("entity_extraction") == "gemini-2.0-flash"
    assert router.route("causal_reasoning") == "claude-opus-4-5"
    assert router.route("voice_transcription") == "whisper-1"


def test_route_unknown_defaults_to_claude():
    router = ModelRouter()
    result = router.route("totally_unknown_task")
    assert result == "claude-opus-4-5"


def test_log_call_and_get_stats(tmp_path):
    router = ModelRouter()
    log_path = tmp_path / "model_call_log.jsonl"
    with patch("backend.tools.model_router._LOG_PATH", log_path):
        router.log_call("entity_extraction", "gemini-2.0-flash", 100, 50, 120, True)
        router.log_call("causal_reasoning", "claude-opus-4-5", 200, 150, 800, True)
        router.log_call("causal_reasoning", "claude-opus-4-5", 200, 0, 500, False)
        stats = router.get_stats()

    assert "gemini-2.0-flash" in stats
    assert stats["gemini-2.0-flash"]["call_count"] == 1
    assert stats["gemini-2.0-flash"]["success_rate"] == 1.0

    assert "claude-opus-4-5" in stats
    assert stats["claude-opus-4-5"]["call_count"] == 2
    assert stats["claude-opus-4-5"]["success_rate"] == 0.5
    assert stats["claude-opus-4-5"]["avg_latency_ms"] == 650


def test_models_status_endpoint(client):
    r = client.get("/models/status")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    names = [m["name"] for m in data["models"]]
    assert "gemini-2.0-flash" in names
    assert "claude-opus-4-5" in names
