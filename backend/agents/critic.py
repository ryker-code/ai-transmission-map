"""
Critic agent: evaluates claim confidence and flags contradictions.
Scorer agent: computes bottleneck scores for affected entities.

Critic uses Claude claude-opus-4-5 for adversarial reasoning.
Scorer uses heuristic scoring with BigQuery/SQLite persistence.
"""
import logging
import uuid
from typing import List
from datetime import datetime, timezone

import time
from backend.config import settings
from backend.tools.model_router import get_router

logger = logging.getLogger(__name__)
_router = get_router()

CRITIC_PROMPT = """You are a skeptical sell-side equity analyst reviewing transmission claims about AI infrastructure.

Your task: evaluate each claim for accuracy, confidence, and consistency.

For each claim, output:
- status: "accepted", "flagged", or "rejected"
  - accepted: claim is well-supported and non-contradictory
  - flagged: claim may be directionally right but confidence should be lowered
  - rejected: claim is unsupported, contradicts known facts, or is too vague
- confidence: adjusted confidence float 0.0-1.0
- critic_note: brief reason for your decision

Be conservative. Reject claims that are obvious, non-falsifiable, or lack specificity.
Flag claims whose confidence seems inflated.

Original analyst note:
{note}

Claims to evaluate:
{claims}

Return the same JSON array with status, confidence, and critic_note added to each claim.
Return ONLY the JSON array."""

# Bottleneck score component weights
WEIGHTS = {
    "evidence_intensity": 0.30,
    "recency_score": 0.20,
    "cross_source_agreement": 0.20,
    "market_confirmation": 0.15,
    "house_view_weight": 0.15,
}


def run_critic(resolved_claims: List[dict], analyst_note: str) -> List[dict]:
    """
    Critic agent: evaluate resolved claims for confidence and validity.
    Uses Claude claude-opus-4-5 for adversarial reasoning.
    Returns claims with status, adjusted confidence, and critic_note fields.
    """
    if not resolved_claims:
        return []

    try:
        from langchain_anthropic import ChatAnthropic
        import json
        model = _router.route("critic_scoring")
        client = ChatAnthropic(
            model=model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.1,
            max_tokens=4096,
        )
        claims_json = json.dumps(resolved_claims, indent=2)
        prompt = CRITIC_PROMPT.format(note=analyst_note, claims=claims_json)
        t0 = time.monotonic()
        response = client.invoke(prompt)
        latency_ms = int((time.monotonic() - t0) * 1000)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        _router.log_call("critic_scoring", model, len(prompt), len(content), latency_ms, True)
        if isinstance(result, list):
            return result
    except Exception as e:
        logger.warning(f"Critic LLM failed ({e}), applying heuristic evaluation")
        _router.log_call("critic_scoring", _router.route("critic_scoring"), 0, 0, 0, False)

    # Heuristic fallback: accept claims with confidence >= 0.6
    critiqued = []
    for claim in resolved_claims:
        c = dict(claim)
        conf = float(c.get("confidence", 0.7))
        if conf >= 0.75:
            c["status"] = "accepted"
            c["critic_note"] = "Heuristic: high confidence, accepted"
        elif conf >= 0.6:
            c["status"] = "flagged"
            c["critic_note"] = "Heuristic: moderate confidence, flagged for review"
        else:
            c["status"] = "rejected"
            c["critic_note"] = "Heuristic: low confidence, rejected"
        critiqued.append(c)
    return critiqued


def _compute_bottleneck_score(entity_name: str, claims: List[dict]) -> dict:
    """
    Compute composite bottleneck score for a single entity from claims it appears in.
    Score = weighted sum of: evidence_intensity, recency, cross_source_agreement,
                              market_confirmation, house_view_weight
    """
    entity_claims = [
        c for c in claims
        if (c.get("subject") == entity_name or c.get("object") == entity_name)
        and c.get("status") != "rejected"
    ]
    if not entity_claims:
        return {}

    n = len(entity_claims)
    avg_confidence = sum(float(c.get("confidence", 0.7)) for c in entity_claims) / n

    # Heuristic component scores
    evidence_intensity = min(1.0, n / 5.0)  # saturates at 5+ claims
    recency_score = avg_confidence  # proxy; real impl uses claim timestamps
    cross_source_agreement = avg_confidence * 0.9
    market_confirmation = avg_confidence * 0.8  # proxy; real impl uses price data

    # Apply analyst house view weight override if set
    try:
        from backend.db.house_view_store import get_weight
        house_view_weight = min(3.0, get_weight(entity_name, default=1.0))
    except Exception:
        house_view_weight = 1.0

    score = (
        WEIGHTS["evidence_intensity"] * evidence_intensity
        + WEIGHTS["recency_score"] * recency_score
        + WEIGHTS["cross_source_agreement"] * cross_source_agreement
        + WEIGHTS["market_confirmation"] * market_confirmation
        + WEIGHTS["house_view_weight"] * house_view_weight
    )

    regime_tags = [c.get("regime_tag", "AI_CAPEX_EXPANSION") for c in entity_claims]
    dominant_regime = max(set(regime_tags), key=regime_tags.count)

    return {
        "id": str(uuid.uuid4()),
        "entity_name": entity_name,
        "score": round(score, 4),
        "evidence_intensity": round(evidence_intensity, 4),
        "recency_score": round(recency_score, 4),
        "cross_source_agreement": round(cross_source_agreement, 4),
        "market_confirmation": round(market_confirmation, 4),
        "house_view_weight": house_view_weight,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "regime_tag": dominant_regime,
    }


def run_scorer(critiqued_claims: List[dict]) -> List[dict]:
    """
    Scorer agent: compute bottleneck scores for all entities affected by the new claims.
    Persists scores to BigQuery (or SQLite stub).
    Returns list of bottleneck score dicts.
    """
    accepted_claims = [c for c in critiqued_claims if c.get("status") != "rejected"]
    if not accepted_claims:
        return []

    # Collect unique entities
    entities = set()
    for claim in accepted_claims:
        if claim.get("subject"):
            entities.add(claim["subject"])
        if claim.get("object"):
            entities.add(claim["object"])

    bottleneck_scores = []
    for entity in entities:
        score_entry = _compute_bottleneck_score(entity, accepted_claims)
        if score_entry:
            bottleneck_scores.append(score_entry)

    # Persist accepted claims so the full scorer can include them in future runs
    try:
        from backend.db.claims_store import add as store_claims
        store_claims(accepted_claims)
    except Exception as e:
        logger.warning(f"Claims store update failed: {e}")

    # Update live regime state with newly accepted claims
    try:
        from backend.tools.regime_detector import add_runtime_claims
        add_runtime_claims(accepted_claims)
    except Exception as e:
        logger.warning(f"Regime update failed: {e}")

    # Persist to DB
    if bottleneck_scores:
        try:
            from backend.config import settings as s
            from backend.db.bigquery_client import BigQueryClient
            client = BigQueryClient(s.google_cloud_project, s.bigquery_dataset)
            rows = [{k: v for k, v in entry.items() if k != "entity_name"} for entry in bottleneck_scores]
            client.insert_rows("bottleneck_scores", rows)
        except Exception as e:
            logger.warning(f"Bottleneck score persistence failed: {e}")

    logger.info(f"Scored {len(bottleneck_scores)} entities")
    return bottleneck_scores
