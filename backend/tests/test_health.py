import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tests.conftest import AUTH_HEADERS

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
    assert len(data["nodes"]) >= 100
    assert len(data["edges"]) >= 30

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
    }, headers=AUTH_HEADERS)
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
    }, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "support_score" in data
    assert "falsification_triggers" in data


def test_thesis_run_returns_falsifiers():
    """Thesis run always returns at least one falsification trigger."""
    response = client.post("/thesis/run", json={
        "thesis": "Constellation Energy will outperform as hyperscalers pay premium for clean firm nuclear power",
        "depth": 2,
    }, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["falsification_triggers"], list)
    assert len(data["falsification_triggers"]) >= 1


def test_memo_generates_text():
    """Memo generation returns non-empty memo_text for any thesis run ID."""
    response = client.post("/memo/generate", json={
        "thesis_run_id": "nonexistent-run-uses-stub-data",
        "style": "internal_brief",
        "max_words": 400,
    }, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "memo_text" in data
    assert len(data["memo_text"]) > 50
    assert "memo_id" in data


def test_regime_detector_returns_dominant():
    """Regime detector returns a recognized regime tag."""
    from backend.tools.regime_detector import detect_regime
    result = detect_regime()
    valid_regimes = {
        "AI_CAPEX_EXPANSION", "SUPPLY_CHAIN_STRESS", "GRID_BOTTLENECK",
        "POWER_PRICE_SPREAD", "REGULATORY", "NUCLEAR_RENAISSANCE",
    }
    assert result["regime"] in valid_regimes
    assert 0 < result["confidence"] <= 1.0
    assert "description" in result


def test_parse_url_endpoint():
    """GET /evidence/parse-url returns metadata for a bloomberg URL."""
    response = client.get("/evidence/parse-url?url=https://www.bloomberg.com/energy/2024-03-15/ge-vernova-transformer-backlog")
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "bloomberg"
    assert data["title"]
    assert data["access_class"] == "metadata_only"
