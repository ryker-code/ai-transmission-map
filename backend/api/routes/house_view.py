import logging
import sqlite3
import os
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
