import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


class RegimeResponse(BaseModel):
    regime: str
    confidence: float
    description: str
    scores: dict


@router.get("/", response_model=RegimeResponse)
async def get_regime():
    """
    Detect and return the dominant market regime from the active claim graph.
    Regime is determined by confidence-weighted claim regime_tag distribution.
    """
    from backend.tools.regime_detector import detect_regime
    result = detect_regime()
    return RegimeResponse(**result)


@router.get("/timeline")
async def get_regime_timeline():
    """
    Return a synthetic regime timeline showing how regime confidence has evolved.
    Uses seed chain snapshots to build a 30-day window with daily granularity.
    """
    from backend.api.schemas import RegimeTimelineResponse, RegimeTimelineEntry
    from backend.tools.regime_detector import detect_regime
    import json
    from pathlib import Path

    chains_path = Path("backend/db/seed_data/transmission_chains.json")
    chains = json.loads(chains_path.read_text()) if chains_path.exists() else []

    REGIMES = ["AI_CAPEX_EXPANSION", "SUPPLY_CHAIN_STRESS", "GRID_BOTTLENECK", "POWER_PRICE_SPREAD", "REGULATORY"]
    REGIME_NOTES = {
        "AI_CAPEX_EXPANSION": "Broad capex acceleration across hyperscalers",
        "SUPPLY_CHAIN_STRESS": "Component lead times extending beyond 52 weeks",
        "GRID_BOTTLENECK": "Utility interconnect queues growing",
        "POWER_PRICE_SPREAD": "Power price differentials widening in key markets",
        "REGULATORY": "FERC/state regulatory actions shaping interconnect",
    }

    # Build tag distribution from seed claims
    tag_counts: dict[str, int] = {}
    tag_conf: dict[str, float] = {}
    for c in chains:
        tag = c.get("regime_tag", "AI_CAPEX_EXPANSION")
        conf = float(c.get("confidence", 0.7))
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        tag_conf[tag] = tag_conf.get(tag, 0.0) + conf

    total_weight = sum(tag_conf.values()) or 1.0

    now = datetime.now(timezone.utc)
    entries = []
    for i in range(30, -1, -1):
        ts = now - timedelta(days=i)
        # Simulate slight drift: regime shifts around i=20 and i=7
        if i > 20:
            dominant = "SUPPLY_CHAIN_STRESS"
            conf = 0.55 + (0.01 * (30 - i))
            count = max(1, len([c for c in chains if c.get("regime_tag") == "SUPPLY_CHAIN_STRESS"]))
        elif i > 7:
            dominant = "AI_CAPEX_EXPANSION"
            conf = 0.60 + (0.01 * (20 - i))
            count = max(1, len([c for c in chains if c.get("regime_tag") == "AI_CAPEX_EXPANSION"]))
        else:
            dominant = "GRID_BOTTLENECK" if i > 3 else "AI_CAPEX_EXPANSION"
            conf = 0.65 + (0.02 * (7 - i))
            count = max(1, len([c for c in chains if c.get("regime_tag") == dominant]))
        entries.append(RegimeTimelineEntry(
            timestamp=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            regime_tag=dominant,
            confidence=round(min(conf, 0.98), 3),
            dominant_claim_count=count,
            note=REGIME_NOTES.get(dominant),
        ))

    current = detect_regime()
    return RegimeTimelineResponse(
        entries=entries,
        current_regime=current["regime"],
        computed_at=now,
    )
