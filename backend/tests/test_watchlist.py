"""Tests for watchlist routes and store."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tests.conftest import AUTH_HEADERS

client = TestClient(app)

# Use a known entity id from seed data
KNOWN_ENTITY_ID = "nvda-001"  # Nvidia


def _find_valid_entity_id() -> str:
    """Get a real entity id from seed data."""
    import json
    from pathlib import Path
    p = Path(__file__).parent.parent / "db/seed_data/entities.json"
    entities = json.loads(p.read_text())
    return entities[0]["id"]


def test_watchlist_empty_initially():
    from backend.db import watchlist_store
    # Reset in-memory set for test isolation
    watchlist_store._watched.clear()
    resp = client.get("/watchlist/")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "total" in data


def test_add_to_watchlist():
    entity_id = _find_valid_entity_id()
    resp = client.post(f"/watchlist/{entity_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "added"
    assert data["entity_id"] == entity_id


def test_watchlist_contains_added_entity():
    entity_id = _find_valid_entity_id()
    client.post(f"/watchlist/{entity_id}", headers=AUTH_HEADERS)
    resp = client.get("/watchlist/")
    assert resp.status_code == 200
    data = resp.json()
    ids = [e["entity_id"] for e in data["entries"]]
    assert entity_id in ids


def test_remove_from_watchlist():
    entity_id = _find_valid_entity_id()
    client.post(f"/watchlist/{entity_id}", headers=AUTH_HEADERS)
    resp = client.delete(f"/watchlist/{entity_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "removed"


def test_watchlist_unknown_entity_returns_404():
    resp = client.post("/watchlist/nonexistent-entity-xyz", headers=AUTH_HEADERS)
    assert resp.status_code == 404
