"""
Full 5-component weighted bottleneck scorer.

Score = weighted sum:
  evidence_intensity    × 0.30  (claim count, saturates at 10)
  recency_score         × 0.20  (exponential decay e^(-days/30); seed claims default 0.5)
  cross_source_agreement × 0.25 (predicate diversity proxy; 3+ distinct predicates → 1.0)
  market_confirmation   × 0.15  (placeholder 0.5; TODO: live price feed)
  house_view_weight     × 0.10  (analyst override 0.1–3.0; neutral = 1.0)

Theoretical max raw score: 1.0*0.30 + 1.0*0.20 + 1.0*0.25 + 1.0*0.15 + 3.0*0.10 = 1.20
Normalized to 0-100: raw / 1.20 * 100
"""
import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.api.schemas import BottleneckEntry

logger = logging.getLogger(__name__)

WEIGHTS = {
    "evidence_intensity": 0.30,
    "recency_score": 0.20,
    "cross_source_agreement": 0.25,
    "market_confirmation": 0.15,
    "house_view_weight": 0.10,
}
MAX_RAW_SCORE = 1.20  # theoretical max when all components at ceiling

_SEED_ENTITIES_PATH = Path("backend/db/seed_data/entities.json")
_SEED_CHAINS_PATH = Path("backend/db/seed_data/transmission_chains.json")


def _load_all_claims() -> list[dict]:
    """Load seed claims plus any runtime pipeline claims."""
    claims: list[dict] = []

    if _SEED_CHAINS_PATH.exists():
        seed = json.loads(_SEED_CHAINS_PATH.read_text())
        # Annotate seed claims as source_type=seed for cross-source computation
        for c in seed:
            c.setdefault("source_type", "seed")
            c.setdefault("status", "accepted")
        claims.extend(seed)

    try:
        from backend.db.claims_store import all_claims
        claims.extend(all_claims())
    except Exception:
        pass

    return claims


def _days_since(iso_ts: Optional[str]) -> float:
    """Return days since an ISO-format timestamp, or 30.0 if unknown."""
    if not iso_ts:
        return 30.0
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return max(0.0, delta.total_seconds() / 86400)
    except Exception:
        return 30.0


def _recency_score(claims: list[dict]) -> float:
    """Exponential decay on most recent claim. Seed claims without timestamp → 0.5."""
    if not claims:
        return 0.0
    timestamps = [c.get("created_at") for c in claims if c.get("created_at")]
    if not timestamps:
        return 0.5  # seed default
    min_days = min(_days_since(ts) for ts in timestamps)
    return round(math.exp(-min_days / 30.0), 4)


def _evidence_intensity(claims: list[dict]) -> float:
    """Saturates at 10 accepted claims → 1.0."""
    return round(min(1.0, len(claims) / 10.0), 4)


def _cross_source_agreement(claims: list[dict]) -> float:
    """
    Proxy: fraction of distinct predicates used (3+ → 1.0).
    In production this would compare source_id uniqueness across claims.
    """
    distinct_predicates = len({c.get("predicate", "") for c in claims if c.get("predicate")})
    distinct_sources = len({c.get("source_type", "seed") for c in claims})
    # Weight both dimensions
    pred_score = min(1.0, distinct_predicates / 3.0)
    src_score = min(1.0, distinct_sources / 2.0)
    return round((pred_score + src_score) / 2.0, 4)


def _market_confirmation() -> float:
    """Placeholder 0.5 — TODO: integrate live price feed."""
    return 0.5


def _house_view_weight(entity_id: str, entity_name: str) -> float:
    """Load analyst house view weight override. Default 1.0 (neutral)."""
    try:
        from backend.db.house_view_store import get_weight
        # Try by ID first, then by name
        w = get_weight(entity_id, default=None)
        if w is None:
            w = get_weight(entity_name, default=1.0)
        return float(w)
    except Exception:
        return 1.0


def compute_bottleneck_scores(entity_ids: Optional[list] = None) -> list[BottleneckEntry]:
    """
    Compute 5-component weighted bottleneck scores for all entities (or a subset).
    Returns a list of BottleneckEntry objects sorted by score descending.
    Scores are normalized to 0-100.
    """
    all_claims = _load_all_claims()
    accepted = [c for c in all_claims if c.get("status", "accepted") != "rejected"]

    if not _SEED_ENTITIES_PATH.exists():
        logger.warning("scorer: entities seed file not found")
        return []

    entities = json.loads(_SEED_ENTITIES_PATH.read_text())
    if entity_ids:
        id_set = set(entity_ids)
        entities = [e for e in entities if e["id"] in id_set]

    results: list[BottleneckEntry] = []

    for entity in entities:
        name = entity["canonical_name"]
        eid = entity["id"]

        entity_claims = [
            c for c in accepted
            if c.get("subject") == name or c.get("object") == name
        ]
        if not entity_claims:
            continue

        ei = _evidence_intensity(entity_claims)
        rs = _recency_score(entity_claims)
        csa = _cross_source_agreement(entity_claims)
        mc = _market_confirmation()
        hvw = _house_view_weight(eid, name)

        raw = (
            WEIGHTS["evidence_intensity"] * ei
            + WEIGHTS["recency_score"] * rs
            + WEIGHTS["cross_source_agreement"] * csa
            + WEIGHTS["market_confirmation"] * mc
            + WEIGHTS["house_view_weight"] * hvw
        )
        normalized = round(min(100.0, raw / MAX_RAW_SCORE * 100.0), 2)

        regime_tags = [c.get("regime_tag", "AI_CAPEX_EXPANSION") for c in entity_claims]
        dominant_regime = max(set(regime_tags), key=regime_tags.count)

        top_evidence = [
            c.get("analyst_note", "")[:120]
            for c in entity_claims
            if c.get("analyst_note")
        ][:3]

        results.append(BottleneckEntry(
            entity_id=eid,
            entity_name=name,
            score=normalized,
            rank=0,  # assigned after sort
            regime_tag=dominant_regime,
            top_evidence=top_evidence,
            components={
                "evidence_intensity": ei,
                "recency_score": rs,
                "cross_source_agreement": csa,
                "market_confirmation": mc,
                "house_view_weight": hvw,
                "raw_score": round(raw, 4),
            },
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    for i, entry in enumerate(results):
        entry.rank = i + 1

    logger.info(f"scorer: scored {len(results)} entities")
    return results
