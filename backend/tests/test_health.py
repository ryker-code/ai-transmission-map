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

def test_bottlenecks_route():
    response = client.get("/bottlenecks/")
    assert response.status_code == 200

def test_evidence_ingest():
    response = client.post("/evidence/", json={
        "url": "https://www.bloomberg.com/test",
        "title": "Test evidence",
        "source_type": "bloomberg",
        "analyst_note": "Transformer lead times now exceeding 120 weeks for large orders",
        "tags": ["transformers", "grid"]
    })
    assert response.status_code == 200
