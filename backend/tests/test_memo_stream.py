"""Tests for streaming memo endpoint."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tests.conftest import AUTH_HEADERS

client = TestClient(app)


def test_stream_endpoint_returns_event_stream():
    """POST /memo/stream returns 200 with text/event-stream content type."""
    resp = client.post(
        "/memo/stream",
        json={"thesis_run_id": "test-run-001", "style": "buyside_lp", "max_words": 200},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_stream_endpoint_emits_data_lines():
    """Stream response contains SSE data lines."""
    resp = client.post(
        "/memo/stream",
        json={"thesis_run_id": "test-run-002", "style": "internal_brief", "max_words": 100},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.text
    assert "data:" in body


def test_stream_endpoint_emits_done_event():
    """Stream response ends with a done:true event."""
    resp = client.post(
        "/memo/stream",
        json={"thesis_run_id": "test-run-003", "style": "sellside_note", "max_words": 100},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    assert '"done": true' in resp.text or '"done":true' in resp.text
