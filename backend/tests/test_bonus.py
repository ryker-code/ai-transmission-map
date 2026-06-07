"""Tests for Bonus features: analysts endpoint, score history, claim feedback."""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.tests.conftest import AUTH_HEADERS

client = TestClient(app)


def test_analysts_endpoint_returns_list():
    resp = client.get("/analysts/")
    assert resp.status_code == 200
    data = resp.json()
    assert "analysts" in data
    assert "total" in data
    assert data["total"] >= 1


_SEED_DIR = Path(__file__).parent.parent / "db/seed_data"


def test_score_history_endpoint():
    entities = json.loads((_SEED_DIR / "entities.json").read_text())
    eid = entities[0]["id"]
    resp = client.get(f"/entities/{eid}/score-history?limit=30")
    assert resp.status_code == 200
    data = resp.json()
    assert "history" in data
    assert "count" in data
    assert "entity_id" in data


def test_claim_feedback_endpoint():
    chains = json.loads((_SEED_DIR / "transmission_chains.json").read_text())
    claim_id = chains[0].get("id", "seed-0")
    resp = client.post(
        f"/claims/{claim_id}/feedback",
        json={"analyst_verdict": "confirm", "note": "Strong evidence for this claim"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "feedback_recorded"
    assert data["verdict"] == "confirm"
    assert data["new_confidence"] >= data["prev_confidence"]


def test_claim_feedback_reject_lowers_confidence():
    chains = json.loads((_SEED_DIR / "transmission_chains.json").read_text())
    claim_id = chains[1].get("id", "seed-1")
    resp = client.post(
        f"/claims/{claim_id}/feedback",
        json={"analyst_verdict": "reject", "note": "Data does not support this claim"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] == "reject"
    assert data["new_confidence"] < data["prev_confidence"] or data["new_confidence"] == 0.10
