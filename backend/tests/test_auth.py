"""Tests for API key authentication on write endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
VALID_KEY = "dev-key-change-in-production"


def test_post_without_key_returns_401():
    resp = client.post(
        "/thesis/run",
        json={"thesis": "Transformer lead times are the binding constraint on AI data center buildout through 2026.", "depth": 1, "include_private": False},
        headers={},
    )
    assert resp.status_code == 401


def test_post_with_valid_key_returns_200():
    resp = client.post(
        "/thesis/run",
        json={"thesis": "Transformer lead times are the binding constraint on AI data center buildout through 2026.", "depth": 1, "include_private": False},
        headers={"X-Api-Key": VALID_KEY},
    )
    assert resp.status_code == 200


def test_get_without_key_returns_200():
    resp = client.get("/bottlenecks/?limit=5")
    assert resp.status_code == 200


def test_health_endpoint_is_public():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_invalid_key_returns_401():
    resp = client.post(
        "/evidence/",
        json={
            "url": "https://bloomberg.com/test",
            "title": "Test Evidence",
            "source_type": "public",
            "analyst_note": "This is a test note that is long enough",
            "tags": [],
            "trust_score": 0.7,
        },
        headers={"X-Api-Key": "wrong-key"},
    )
    assert resp.status_code == 401
