"""
House view agent: applies analyst conviction overrides to bottleneck scores.

Rules:
- weight_override (0.1–3.0) multiplies the house_view_weight component
- conviction = "high": adds 0.10 bonus to final normalized score (before 100 ceiling)
- conviction = "low":  subtracts 0.10 from final normalized score (floor at 0)
- pinned_thesis: entity added to pinned list in output
"""
import logging
from typing import Optional

from backend.api.schemas import BottleneckEntry, BottlenecksResponse
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CONVICTION_BONUS = {
    "high": 10.0,   # +10 points (on 0-100 scale)
    "medium": 0.0,
    "low": -10.0,
}


def apply_house_view(scores: list[BottleneckEntry]) -> tuple[list[BottleneckEntry], list[str]]:
    """
    Apply house view conviction overrides to a list of BottleneckEntry objects.

    Returns (adjusted_scores, pinned_entity_ids).
    Adjustments are applied in-place to copies of the entries.
    """
    try:
        from backend.db.house_view_store import all_entries as hv_entries
        views = hv_entries()
    except Exception as e:
        logger.warning(f"house_view_store unavailable: {e}")
        views = {}

    pinned: list[str] = []
    adjusted: list[BottleneckEntry] = []

    for entry in scores:
        eid = entry.entity_id
        view = views.get(eid)

        if view is None:
            adjusted.append(entry)
            continue

        # Clone the components dict so we don't mutate the original
        components = dict(entry.components)

        weight_override = float(view.get("weight_override", 1.0))
        weight_override = max(0.1, min(3.0, weight_override))

        # Adjust house_view_weight component
        original_hvw = float(components.get("house_view_weight", 1.0))
        components["house_view_weight"] = round(original_hvw * weight_override, 4)
        components["conviction"] = view.get("conviction", "medium")
        components["weight_override_applied"] = weight_override

        # Recompute score from raw_score if available, else adjust proportionally
        raw = components.get("raw_score")
        if raw is not None:
            # Subtract old house_view contribution and add new
            old_hvw_contrib = original_hvw * 0.10
            new_hvw_contrib = components["house_view_weight"] * 0.10
            new_raw = float(raw) - old_hvw_contrib + new_hvw_contrib
            base_score = min(100.0, new_raw / 1.20 * 100.0)
            components["raw_score"] = round(new_raw, 4)
        else:
            base_score = entry.score

        # Apply conviction bonus/malus (on 0-100 scale)
        conviction = view.get("conviction", "medium")
        bonus = CONVICTION_BONUS.get(conviction, 0.0)
        final_score = round(max(0.0, min(100.0, base_score + bonus)), 2)

        # Track pinned entities
        if view.get("pinned_thesis"):
            pinned.append(eid)

        adjusted.append(BottleneckEntry(
            entity_id=entry.entity_id,
            entity_name=entry.entity_name,
            score=final_score,
            rank=entry.rank,
            regime_tag=entry.regime_tag,
            top_evidence=entry.top_evidence,
            components=components,
        ))

    # Re-sort and re-rank after adjustments
    adjusted.sort(key=lambda x: x.score, reverse=True)
    for i, entry in enumerate(adjusted):
        entry.rank = i + 1

    logger.info(f"house_view: adjusted {sum(1 for e in adjusted if e.entity_id in views)} entries, {len(pinned)} pinned")
    return adjusted, pinned
