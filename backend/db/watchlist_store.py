"""In-memory watchlist store, persisted to SQLite watchlist table."""
import logging
import sqlite3
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent / "local/aitm_stub.db"
_watched: set[str] = set()
_loaded = False


def _ensure_table() -> None:
    os.makedirs(_DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        entity_id TEXT PRIMARY KEY,
        added_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit()
    conn.close()


def _load_from_sqlite() -> None:
    global _loaded
    if _loaded:
        return
    _ensure_table()
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        rows = conn.execute("SELECT entity_id FROM watchlist").fetchall()
        conn.close()
        for (eid,) in rows:
            _watched.add(eid)
    except Exception as exc:
        logger.warning(f"watchlist_store: failed to load from SQLite: {exc}")
    _loaded = True


def add(entity_id: str) -> None:
    _load_from_sqlite()
    _watched.add(entity_id)
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (entity_id) VALUES (?)", (entity_id,)
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning(f"watchlist_store add SQLite error: {exc}")


def remove(entity_id: str) -> None:
    _load_from_sqlite()
    _watched.discard(entity_id)
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute("DELETE FROM watchlist WHERE entity_id = ?", (entity_id,))
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning(f"watchlist_store remove SQLite error: {exc}")


def list_watched() -> list[str]:
    _load_from_sqlite()
    return sorted(_watched)


def is_watched(entity_id: str) -> bool:
    _load_from_sqlite()
    return entity_id in _watched
