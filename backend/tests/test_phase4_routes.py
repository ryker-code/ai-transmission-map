"""Tests for Phase 3-7 routes: entity detail, regime timeline, claims audit, PDF export, house view narrative."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from backend.main import app
    return TestClient(app)


# --- Entity detail ---

def test_entity_detail_not_found(client):
    r = client.get("/entities/nonexistent-id-xyz")
    assert r.status_code == 404


def test_entity_list_with_search(client):
    r = client.get("/entities/?search=nvidia&limit=5")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_entity_list_empty_search(client):
    r = client.get("/entities/?search=zzz_no_match_xyz")
    assert r.status_code == 200
    assert r.json() == []


def test_entity_detail_first_entity(client):
    """Fetch first entity from list, then get its detail."""
    r = client.get("/entities/?limit=1")
    assert r.status_code == 200
    entities = r.json()
    if not entities:
        pytest.skip("No seed entities available")
    eid = entities[0]["id"]
    r2 = client.get(f"/entities/{eid}")
    assert r2.status_code == 200
    d = r2.json()
    assert "canonical_name" in d
    assert "outbound_claims" in d
    assert "inbound_claims" in d
    assert "related_entities" in d


# --- Regime timeline ---

def test_regime_timeline(client):
    r = client.get("/regime/timeline")
    assert r.status_code == 200
    d = r.json()
    assert "entries" in d
    assert "current_regime" in d
    assert len(d["entries"]) == 31  # 30 days back + today


def test_regime_timeline_confidence_range(client):
    r = client.get("/regime/timeline")
    assert r.status_code == 200
    for entry in r.json()["entries"]:
        assert 0.0 <= entry["confidence"] <= 1.0


# --- Claims audit ---

def test_claim_audit_not_found(client):
    r = client.get("/claims/nonexistent-claim-id/evidence")
    assert r.status_code == 404


def test_claim_audit_seed_claim(client):
    """Fetch first seed chain by its actual ID and verify audit structure."""
    import json
    from pathlib import Path
    chains = json.loads((Path(__file__).parent.parent / "db/seed_data/transmission_chains.json").read_text())
    if not chains:
        pytest.skip("No seed chains available")
    first_id = chains[0].get("id", "seed-0")
    r = client.get(f"/claims/{first_id}/evidence")
    assert r.status_code == 200
    d = r.json()
    assert "claim_id" in d
    assert "evidence" in d
    assert "analyst_summary" in d
    assert d["supporting_sources"] >= 1


# --- House view narrative ---

def test_house_view_narrative_no_entries(client):
    r = client.get("/house-view/narrative")
    assert r.status_code == 200
    d = r.json()
    assert "narrative" in d
    assert len(d["narrative"]) > 50


def test_house_view_narrative_cached(client):
    """Second call within TTL should return cached=True."""
    client.get("/house-view/narrative")
    r2 = client.get("/house-view/narrative")
    assert r2.status_code == 200
    assert r2.json().get("cached") is True


# --- PDF export ---

def test_pdf_export_unknown_memo(client):
    """Unknown memo ID should return stub PDF bytes."""
    r = client.get("/memo/aaaaaaaa-0000-0000-0000-000000000000/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 100


def test_pdf_export_tool_directly():
    """Direct test of generate_memo_pdf."""
    from backend.tools.pdf_export import generate_memo_pdf
    memo = {
        "memo_id": "test-123",
        "memo_text": "Test memo content.\n\nSecond paragraph.",
        "regime": "AI_CAPEX_EXPANSION",
        "key_bottlenecks": ["Transformer Lead Times"],
        "affected_names": ["GE Vernova"],
        "model_used": "claude-opus-4-5",
    }
    pdf = generate_memo_pdf(memo, "Test thesis")
    assert pdf[:4] == b"%PDF"
