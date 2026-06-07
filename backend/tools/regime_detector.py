"""
Regime detector: computes the dominant market regime from the active claims in the graph.
Regime is the most-weighted regime_tag across recent high-confidence claims.
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Runtime claims appended by the pipeline scorer; included in regime computation alongside seed data.
_dynamic_claims: list = []


def add_runtime_claims(claims: list) -> None:
    """Append pipeline-extracted claims to the dynamic claim pool for live regime updates."""
    _dynamic_claims.extend(claims)
    logger.debug(f"regime_detector: added {len(claims)} runtime claims (total={len(_dynamic_claims)})")


REGIME_DESCRIPTIONS = {
    "AI_CAPEX_EXPANSION": "Hyperscaler capex is expanding rapidly; GPU clusters, data centers, and power infrastructure are all in demand surge.",
    "SUPPLY_CHAIN_STRESS": "Transformer, HBM memory, or other supply chain bottlenecks are the binding constraint on AI infrastructure growth.",
    "GRID_BOTTLENECK": "Utility interconnection queues and grid capacity are the primary rate-limiters on data center expansion.",
    "POWER_PRICE_SPREAD": "Merchant power price spreads are wide; AI load growth is driving real-time power price volatility in key RTOs.",
    "REGULATORY": "Regulatory actions (FERC, NERC, EPA, DOE) are the dominant near-term risk factor for infrastructure investment.",
    "NUCLEAR_RENAISSANCE": "Nuclear PPAs with hyperscalers are the dominant new power procurement trend; nuclear operators are outperforming.",
}


def detect_regime(regime_filter: Optional[str] = None) -> dict:
    """
    Detect the dominant regime from seed/live claim data.
    Returns regime tag, description, confidence, and per-regime scores.
    """
    chains_path = Path("backend/db/seed_data/transmission_chains.json")
    if not chains_path.exists():
        return {"regime": "AI_CAPEX_EXPANSION", "confidence": 0.7, "description": REGIME_DESCRIPTIONS["AI_CAPEX_EXPANSION"], "scores": {}}

    chains = json.loads(chains_path.read_text()) + _dynamic_claims

    # Weight by confidence
    regime_scores: dict = {}
    for chain in chains:
        tag = chain.get("regime_tag", "AI_CAPEX_EXPANSION")
        weight = float(chain.get("confidence", 0.7))
        regime_scores[tag] = regime_scores.get(tag, 0.0) + weight

    if not regime_scores:
        return {"regime": "AI_CAPEX_EXPANSION", "confidence": 0.7, "description": REGIME_DESCRIPTIONS["AI_CAPEX_EXPANSION"], "scores": {}}

    total = sum(regime_scores.values())
    normalized = {k: round(v / total, 4) for k, v in regime_scores.items()}

    dominant = max(normalized, key=normalized.get)
    confidence = normalized[dominant]

    return {
        "regime": dominant,
        "confidence": round(confidence, 4),
        "description": REGIME_DESCRIPTIONS.get(dominant, ""),
        "scores": normalized,
    }
