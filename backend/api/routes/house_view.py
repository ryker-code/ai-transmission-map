import logging
import sqlite3
import os
import time
from fastapi import APIRouter
from backend.api.schemas import HouseViewUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

_DB_PATH = "backend/db/local/aitm_stub.db"


def _persist_to_sqlite(payload: HouseViewUpdate) -> None:
    """Persist house view override to SQLite stub for session durability."""
    try:
        os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS house_view (
                entity_id TEXT PRIMARY KEY,
                weight_override REAL,
                conviction TEXT,
                analyst_note TEXT,
                pinned_thesis TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO house_view (entity_id, weight_override, conviction, analyst_note, pinned_thesis, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(entity_id) DO UPDATE SET
                weight_override=excluded.weight_override,
                conviction=excluded.conviction,
                analyst_note=excluded.analyst_note,
                pinned_thesis=excluded.pinned_thesis,
                updated_at=excluded.updated_at
        """, (payload.entity_id, payload.weight_override, payload.conviction,
              payload.analyst_note, payload.pinned_thesis))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"SQLite house_view persist failed: {e}")


@router.put("/", response_model=dict)
async def update_house_view(payload: HouseViewUpdate):
    """
    Update analyst conviction weight and annotations for an entity.
    Persists to in-memory store and SQLite stub. Triggers scorer re-run.
    """
    from backend.db.house_view_store import put as store_view
    store_view(payload.entity_id, {
        "weight_override": payload.weight_override,
        "conviction": payload.conviction,
        "analyst_note": payload.analyst_note,
        "pinned_thesis": payload.pinned_thesis,
    })
    _persist_to_sqlite(payload)
    logger.info(f"House view updated: entity={payload.entity_id} weight={payload.weight_override} conviction={payload.conviction}")
    return {
        "status": "updated",
        "entity_id": payload.entity_id,
        "weight_override": payload.weight_override,
        "conviction": payload.conviction,
    }


@router.get("/", response_model=dict)
async def list_house_views():
    """Return all active analyst house view overrides."""
    from backend.db.house_view_store import all_entries
    entries = all_entries()
    return {"house_views": entries, "total": len(entries)}


_narrative_cache: dict = {"text": None, "ts": 0.0}
_NARRATIVE_TTL = 300  # 5-minute cache


@router.get("/narrative", response_model=dict)
async def get_house_view_narrative():
    """
    Generate a 3-paragraph analyst narrative describing the current house view
    positioning across the AI infrastructure transmission chain.
    Cached for 5 minutes to avoid repeated LLM calls.
    """
    from backend.db.house_view_store import all_entries
    from backend.config import settings

    now = time.time()
    if _narrative_cache["text"] and (now - _narrative_cache["ts"]) < _NARRATIVE_TTL:
        return {"narrative": _narrative_cache["text"], "cached": True}

    entries = all_entries()
    if not entries:
        narrative = (
            "The current house view has no active overrides. All entities in the AI transmission "
            "graph are weighted at parity (1.0×). The dominant regime is AI_CAPEX_EXPANSION, "
            "with transformer lead times and grid interconnection as the primary structural constraints.\n\n"
            "Without analyst conviction adjustments, bottleneck scores reflect the raw evidence intensity "
            "and cross-source agreement from inbound claims. Power infrastructure and semiconductor memory "
            "supply chains remain the two most data-rich bottleneck clusters.\n\n"
            "To express a view, use the House View panel to set conviction (high/low) and weight overrides "
            "on specific entities. High conviction adds +10 pts to bottleneck score; low conviction subtracts 10 pts."
        )
        _narrative_cache.update({"text": narrative, "ts": now})
        return {"narrative": narrative, "cached": False}

    # Build context for LLM
    high = [(eid, d) for eid, d in entries.items() if d.get("conviction") == "high"]
    low = [(eid, d) for eid, d in entries.items() if d.get("conviction") == "low"]
    medium = [(eid, d) for eid, d in entries.items() if d.get("conviction") == "medium"]

    context = f"High conviction ({len(high)}): {', '.join(eid for eid, _ in high[:5])}\n"
    context += f"Low conviction ({len(low)}): {', '.join(eid for eid, _ in low[:5])}\n"
    context += f"Medium ({len(medium)}): {', '.join(eid for eid, _ in medium[:5])}"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        prompt = (
            f"You are a senior equity analyst writing a 3-paragraph house view narrative for an investor. "
            f"The AI infrastructure transmission map shows these conviction positions:\n{context}\n\n"
            f"Write exactly 3 paragraphs: (1) Overall positioning and dominant theme, "
            f"(2) Key overweights and why they appear in the AI infrastructure chain, "
            f"(3) Key underweights and falsification risks. Be specific, concise, and investor-grade. "
            f"No headers or bullet points — flowing prose only."
        )
        if "placeholder" in settings.anthropic_api_key.lower():
            raise ValueError("placeholder key")
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        narrative = resp.content[0].text
    except Exception as e:
        logger.warning(f"House view narrative LLM call failed: {e}")
        high_names = ", ".join(eid for eid, _ in high[:3]) or "none set"
        low_names = ", ".join(eid for eid, _ in low[:3]) or "none set"
        narrative = (
            f"The current house view expresses high conviction on {high_names} — entities at the "
            f"intersection of AI capex growth and constrained supply. Power infrastructure and "
            f"transformer manufacturers are primary overweights given 80-120 week lead times.\n\n"
            f"Underweights include {low_names}, where near-term catalysts appear insufficient relative "
            f"to the current bottleneck score. Regulatory risk and interconnection queue uncertainty "
            f"add friction to the long-duration infrastructure thesis.\n\n"
            f"Key falsification risk: faster-than-expected Asian transformer import ramp or FERC Order 2023 "
            f"reforms could rapidly shift the regime toward SUPPLY_CHAIN_STRESS alleviation. Monitor "
            f"weekly transformer order data from AWEA and interconnection queue statistics from LBNL."
        )

    _narrative_cache.update({"text": narrative, "ts": now})
    return {"narrative": narrative, "cached": False}
