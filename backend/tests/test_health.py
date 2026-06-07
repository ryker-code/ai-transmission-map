import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_graph_route():
    response = client.get("/graph/")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 100
    assert len(data["edges"]) == 30

def test_graph_regime_filter():
    response = client.get("/graph/?regime=AI_CAPEX_EXPANSION")
    assert response.status_code == 200
    data = response.json()
    assert data["regime_tag"] == "AI_CAPEX_EXPANSION"

def test_bottlenecks_route():
    response = client.get("/bottlenecks/")
    assert response.status_code == 200
    data = response.json()
    assert "bottlenecks" in data
    assert data["total"] > 0

def test_bottlenecks_limit():
    response = client.get("/bottlenecks/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["bottlenecks"]) <= 5

def test_evidence_ingest():
    response = client.post("/evidence/", json={
        "url": "https://www.bloomberg.com/test",
        "title": "Test evidence",
        "source_type": "bloomberg",
        "analyst_note": "Transformer lead times now exceeding 120 weeks for large orders",
        "tags": ["transformers", "grid"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert "source_id" in data

def test_regime_route():
    response = client.get("/regime/")
    assert response.status_code == 200
    data = response.json()
    assert "regime" in data
    assert "confidence" in data
    assert data["confidence"] > 0

def test_thesis_run():
    response = client.post("/thesis/run", json={
        "thesis": "Transformer lead times will keep GE Vernova backlog elevated through 2026 supporting margin expansion",
        "depth": 2,
        "include_private": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "support_score" in data
    assert "falsification_triggers" in data
