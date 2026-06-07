"""Tests for DBRouter: SQLite fallback, entity count, claim insert, health endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_db_router_sqlite_fallback():
    from backend.db.db_router import get_db_router
    router = get_db_router()
    assert router.active == "sqlite"
    assert router.bq.available is False


def test_db_router_entity_count():
    from backend.db.db_router import get_db_router
    router = get_db_router()
    count = router.entity_count()
    assert count >= 200


def test_db_router_claim_count():
    from backend.db.db_router import get_db_router
    router = get_db_router()
    count = router.claim_count()
    assert count >= 80


def test_db_router_insert_claim():
    from backend.db.db_router import get_db_router
    router = get_db_router()
    router.insert_claim({
        "id": "test-claim-999",
        "subject": "Nvidia",
        "predicate": "supplies_gpus_to",
        "object": "Hyperscaler GPU Clusters",
        "confidence": 0.9,
    })
    # No exception = success


def test_health_db_endpoint():
    resp = client.get("/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["db_active"] in ("sqlite", "bigquery")
    assert isinstance(data["bq_available"], bool)
    assert data["entity_count"] >= 200
    assert data["claim_count"] >= 80
    assert data["uptime_seconds"] >= 0


def test_health_endpoint_enriched():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["db"] in ("sqlite", "bigquery")
    assert data["entity_count"] >= 200
    assert data["claim_count"] >= 80
