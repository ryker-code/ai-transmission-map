import json
import logging
from pathlib import Path
from fastapi import APIRouter, Query
from backend.api.schemas import BottlenecksResponse, BottleneckEntry
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()


def _compute_static_bottlenecks(limit: int) -> list:
    """
    Compute bottleneck scores from seed data using heuristic scoring.
    Real implementation will query BigQuery bottleneck_scores table.
    Score = weighted average of claim confidence for each entity.
    """
    entities_path = Path("backend/db/seed_data/entities.json")
    chains_path = Path("backend/db/seed_data/transmission_chains.json")
    if not entities_path.exists() or not chains_path.exists():
        return []

    entities = json.loads(entities_path.read_text())
    chains = json.loads(chains_path.read_text())

    entity_index = {e["canonical_name"]: e for e in entities}

    # Score each entity by how many chains they appear in and avg confidence
    scores: dict = {}
    evidence: dict = {}
    for chain in chains:
        for role in ["subject", "object"]:
            name = chain[role]
            if name not in scores:
                scores[name] = {"total_confidence": 0.0, "count": 0, "regime_tags": []}
                evidence[name] = []
            scores[name]["total_confidence"] += chain["confidence"]
            scores[name]["count"] += 1
            scores[name]["regime_tags"].append(chain.get("regime_tag", "AI_CAPEX_EXPANSION"))
            if chain.get("analyst_note"):
                evidence[name].append(chain["analyst_note"][:120])

    entries = []
    for i, (name, data) in enumerate(
        sorted(scores.items(), key=lambda x: x[1]["total_confidence"] / max(x[1]["count"], 1), reverse=True)
    ):
        if i >= limit:
            break
        avg = data["total_confidence"] / max(data["count"], 1)
        regime_counts: dict = {}
        for tag in data["regime_tags"]:
            regime_counts[tag] = regime_counts.get(tag, 0) + 1
        dominant_regime = max(regime_counts, key=regime_counts.get)
        entity = entity_index.get(name, {})

        # Apply house view weight override
        house_weight = 1.0
        try:
            from backend.db.house_view_store import get_weight
            house_weight = get_weight(entity.get("id", name), default=1.0)
        except Exception:
            pass
        weighted_score = min(1.0, round(avg * house_weight, 4))

        entries.append(BottleneckEntry(
            entity_id=entity.get("id", name),
            entity_name=name,
            score=weighted_score,
            rank=i + 1,
            regime_tag=dominant_regime,
            top_evidence=evidence[name][:3],
            components={
                "evidence_intensity": round(min(1.0, data["count"] / 5.0), 4),
                "avg_confidence": round(avg, 4),
                "claim_count": data["count"],
                "house_view_weight": house_weight,
            },
        ))

    return entries


@router.get("/", response_model=BottlenecksResponse)
async def get_bottlenecks(
    limit: int = Query(20, ge=1, le=100),
    regime: str = Query(None, description="Filter by regime tag"),
):
    """Return ranked bottleneck nodes by composite score."""
    try:
        bottlenecks = _compute_static_bottlenecks(limit * 3)  # over-fetch for filtering
        if regime:
            bottlenecks = [b for b in bottlenecks if b.regime_tag == regime]
        bottlenecks = bottlenecks[:limit]
        # Re-rank after filter
        for i, b in enumerate(bottlenecks):
            b.rank = i + 1
        return BottlenecksResponse(
            bottlenecks=bottlenecks,
            total=len(bottlenecks),
            computed_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"Bottlenecks query failed: {e}")
        return BottlenecksResponse(bottlenecks=[], total=0, computed_at=datetime.now(timezone.utc))
