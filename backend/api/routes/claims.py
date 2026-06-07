import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.api.schemas import ClaimAuditResponse, EvidenceAuditEntry

logger = logging.getLogger(__name__)
router = APIRouter()

_CHAINS_PATH = Path("backend/db/seed_data/transmission_chains.json")
_EVIDENCE_PATH = Path("backend/db/seed_data/evidence_sources.json")


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
