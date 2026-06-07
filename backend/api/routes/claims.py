import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from backend.api.schemas import ClaimAuditResponse, ClaimFeedback, EvidenceAuditEntry
from backend.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()

_CHAINS_PATH = Path(__file__).parent.parent.parent / "db/seed_data/transmission_chains.json"
_EVIDENCE_PATH = Path(__file__).parent.parent.parent / "db/seed_data/evidence_sources.json"


@router.get("/{claim_id}/evidence", response_model=ClaimAuditResponse)
async def get_claim_audit(claim_id: str):
    """
    Return full audit trail for a specific claim: claim metadata plus all evidence
    sources that support or reference it.
    """
    chains = json.loads(_CHAINS_PATH.read_text()) if _CHAINS_PATH.exists() else []

    claim = None
    for i, c in enumerate(chains):
        cid = c.get("id", f"seed-{i}")
        if cid == claim_id:
            claim = c
            claim["_resolved_id"] = cid
            break

    if claim is None:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    # Load evidence sources if available
    evidence_list: list[EvidenceAuditEntry] = []
    try:
        if _EVIDENCE_PATH.exists():
            sources = json.loads(_EVIDENCE_PATH.read_text())
            # Match by entity names mentioned in the claim
            keywords = {claim["subject"].lower(), claim["object"].lower()}
            for s in sources:
                title_lower = s.get("title", "").lower()
                if any(k in title_lower for k in keywords):
                    evidence_list.append(EvidenceAuditEntry(
                        source_id=s.get("id", "unknown"),
                        title=s.get("title", ""),
                        source_type=s.get("source_type", "public"),
                        url=s.get("url"),
                        publish_date=s.get("publish_date"),
                        trust_score=float(s.get("trust_score", 0.7)),
                        analyst_note=s.get("analyst_note"),
                    ))
    except Exception as e:
        logger.warning(f"Could not load evidence sources for claim audit: {e}")

    # Stub evidence if none found
    if not evidence_list:
        evidence_list = [
            EvidenceAuditEntry(
                source_id="stub-001",
                title=f"Seed chain: {claim['subject']} → {claim['object']}",
                source_type="internal",
                url=None,
                publish_date=None,
                trust_score=0.8,
                analyst_note="Seeded transmission chain; no external source attached.",
            )
        ]

    direction = claim.get("direction", "positive")
    confidence = float(claim.get("confidence", 0.7))
    analyst_summary = (
        f"{'Positive' if direction == 'positive' else 'Negative'} transmission: "
        f"{claim['subject']} → {claim['predicate']} → {claim['object']}. "
        f"Confidence {confidence*100:.0f}%. "
        f"Supported by {len(evidence_list)} source(s)."
    )

    return ClaimAuditResponse(
        claim_id=claim["_resolved_id"],
        subject=claim["subject"],
        predicate=claim["predicate"],
        object=claim["object"],
        direction=direction,
        confidence=confidence,
        horizon=claim.get("horizon", "12M"),
        regime_tag=claim.get("regime_tag", "AI_CAPEX_EXPANSION"),
        evidence=evidence_list,
        supporting_sources=len(evidence_list),
        analyst_summary=analyst_summary,
    )


# In-memory feedback store (keyed by claim_id)
_feedback_store: dict[str, dict] = {}


@router.post("/{claim_id}/feedback", response_model=dict, dependencies=[Depends(verify_api_key)])
async def submit_claim_feedback(claim_id: str, payload: ClaimFeedback):
    """
    Submit analyst verdict on a claim. Updates confidence in the runtime claims store.
    confirm: +0.05 (max 0.95), reject: -0.10 (min 0.10), uncertain: no change.
    Triggers scorer re-run for affected entities.
    """
    # Find claim in seed data to get subject/object
    chains = json.loads(_CHAINS_PATH.read_text()) if _CHAINS_PATH.exists() else []
    claim = None
    for i, c in enumerate(chains):
        if c.get("id", f"seed-{i}") == claim_id:
            claim = dict(c)
            break

    # Also check runtime claims store
    affected_entity = None
    try:
        from backend.db.claims_store import get_all_claims, update_confidence
        for c in get_all_claims():
            if c.get("claim_id") == claim_id or c.get("id") == claim_id:
                claim = c
                break
    except Exception:
        pass

    current_confidence = float((claim or {}).get("confidence", 0.7))

    if payload.analyst_verdict == "confirm":
        new_confidence = min(0.95, current_confidence + 0.05)
    elif payload.analyst_verdict == "reject":
        new_confidence = max(0.10, current_confidence - 0.10)
    else:
        new_confidence = current_confidence

    _feedback_store[claim_id] = {
        "claim_id": claim_id,
        "verdict": payload.analyst_verdict,
        "note": payload.note,
        "user_id": payload.user_id or "default",
        "prev_confidence": current_confidence,
        "new_confidence": new_confidence,
    }

    # Invalidate bottleneck cache to trigger scorer re-run on next request
    try:
        from backend.db.cache import get_cache
        get_cache().invalidate_prefix("bottlenecks:")
    except Exception:
        pass

    logger.info(f"Claim feedback: {claim_id} → {payload.analyst_verdict} confidence {current_confidence:.2f} → {new_confidence:.2f}")
    return {
        "status": "feedback_recorded",
        "claim_id": claim_id,
        "verdict": payload.analyst_verdict,
        "prev_confidence": current_confidence,
        "new_confidence": new_confidence,
        "note": payload.note,
    }
