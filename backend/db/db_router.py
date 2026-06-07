"""Routes DB calls to BigQuery or SQLite/seed-JSON based on availability."""
import json
import logging
import sqlite3
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_ENTITIES_PATH = Path(__file__).parent / "seed_data/entities.json"
_CHAINS_PATH = Path(__file__).parent / "seed_data/transmission_chains.json"
_DB_PATH = Path(__file__).parent / "local/aitm_stub.db"


class _SqliteFallback:
    """Thin wrapper around seed JSON + SQLite for local dev."""

    def __init__(self):
        self._entities: list[dict] = []
        self._chains: list[dict] = []
        self._load_seed()
        self._ensure_sqlite()

    def _load_seed(self):
        if _ENTITIES_PATH.exists():
            self._entities = json.loads(_ENTITIES_PATH.read_text())
        if _CHAINS_PATH.exists():
            self._chains = json.loads(_CHAINS_PATH.read_text())

    def _ensure_sqlite(self):
        os.makedirs(_DB_PATH.parent, exist_ok=True)
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute("""CREATE TABLE IF NOT EXISTS house_view (
            entity_id TEXT PRIMARY KEY,
            weight_override REAL,
            conviction TEXT,
            analyst_note TEXT,
            pinned_thesis TEXT,
            updated_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS watchlist (
            entity_id TEXT PRIMARY KEY,
            added_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS evidence_log (
            id TEXT PRIMARY KEY,
            source_text TEXT,
            inserted_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS claims_log (
            id TEXT PRIMARY KEY,
            subject TEXT,
            predicate TEXT,
            object TEXT,
            confidence REAL,
            inserted_at TEXT
        )""")
        conn.commit()
        conn.close()

    def get_entities(self, sector=None, entity_type=None, search=None) -> list:
        rows = self._entities[:]
        if sector:
            rows = [e for e in rows if e.get("sector") == sector]
        if entity_type:
            rows = [e for e in rows if e.get("entity_type") == entity_type]
        if search:
            q = search.lower()
            rows = [
                e for e in rows
                if q in e["canonical_name"].lower()
                or any(q in a.lower() for a in e.get("aliases", []))
                or (e.get("ticker") and q in e["ticker"].lower())
            ]
        return rows

    def get_claims(self, regime=None, entity_id=None) -> list:
        rows = self._chains[:]
        if regime:
            rows = [c for c in rows if c.get("regime_tag") == regime]
        if entity_id:
            entity_name = next(
                (e["canonical_name"] for e in self._entities if e["id"] == entity_id), None
            )
            if entity_name:
                rows = [c for c in rows if c["subject"] == entity_name or c["object"] == entity_name]
        return rows

    def get_bottleneck_scores(self) -> list:
        # Delegated to scorer agent — return empty here; scorer reads seed directly
        return []

    def upsert_house_view(self, record: dict) -> None:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute("""
            INSERT INTO house_view (entity_id, weight_override, conviction, analyst_note, pinned_thesis, updated_at)
            VALUES (:entity_id, :weight_override, :conviction, :analyst_note, :pinned_thesis, :updated_at)
            ON CONFLICT(entity_id) DO UPDATE SET
                weight_override=excluded.weight_override,
                conviction=excluded.conviction,
                analyst_note=excluded.analyst_note,
                pinned_thesis=excluded.pinned_thesis,
                updated_at=excluded.updated_at
        """, {**record, "updated_at": datetime.now(timezone.utc).isoformat()})
        conn.commit()
        conn.close()

    def insert_evidence(self, record: dict) -> None:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute(
            "INSERT OR IGNORE INTO evidence_log (id, source_text, inserted_at) VALUES (?, ?, ?)",
            (record.get("id", ""), record.get("source_text", ""), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()

    def insert_claim(self, record: dict) -> None:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.execute(
            "INSERT OR IGNORE INTO claims_log (id, subject, predicate, object, confidence, inserted_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                record.get("id", ""),
                record.get("subject", ""),
                record.get("predicate", ""),
                record.get("object", ""),
                record.get("confidence", 0.0),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def entity_count(self) -> int:
        return len(self._entities)

    def claim_count(self) -> int:
        return len(self._chains)


class DBRouter:
    """Routes DB operations to BigQuery (when available) or SQLite/seed fallback."""

    def __init__(self):
        from backend.db.bq_client import get_bq_client
        self.bq = get_bq_client()
        self._sqlite = _SqliteFallback()
        self.active = "bigquery" if self.bq.available else "sqlite"
        logger.info(f"DBRouter active backend: {self.active}")

    # ── Read methods ──────────────────────────────────────────────────────────

    def get_entities(self, sector=None, entity_type=None, search=None) -> list:
        """Return entities from active backend."""
        if self.active == "bigquery":
            try:
                sql = f"SELECT * FROM `{self.bq.project}.{self.bq.dataset}.entities` WHERE 1=1"
                if sector:
                    sql += f" AND sector = '{sector}'"
                if entity_type:
                    sql += f" AND entity_type = '{entity_type}'"
                return self.bq.query(sql)
            except Exception as exc:
                logger.warning(f"BQ get_entities failed, falling back: {exc}")
        return self._sqlite.get_entities(sector=sector, entity_type=entity_type, search=search)

    def get_claims(self, regime=None, entity_id=None) -> list:
        """Return transmission claims from active backend."""
        if self.active == "bigquery":
            try:
                sql = f"SELECT * FROM `{self.bq.project}.{self.bq.dataset}.transmission_chains`"
                return self.bq.query(sql)
            except Exception as exc:
                logger.warning(f"BQ get_claims failed, falling back: {exc}")
        return self._sqlite.get_claims(regime=regime, entity_id=entity_id)

    def get_bottleneck_scores(self) -> list:
        """Return bottleneck scores (always delegated to scorer agent)."""
        return self._sqlite.get_bottleneck_scores()

    # ── Write methods ─────────────────────────────────────────────────────────

    def upsert_house_view(self, record: dict) -> None:
        if self.active == "bigquery":
            try:
                self.bq.insert_rows("house_view", [record])
                return
            except Exception as exc:
                logger.warning(f"BQ upsert_house_view failed, falling back: {exc}")
        self._sqlite.upsert_house_view(record)

    def insert_evidence(self, record: dict) -> None:
        if self.active == "bigquery":
            try:
                self.bq.insert_rows("evidence", [record])
                return
            except Exception as exc:
                logger.warning(f"BQ insert_evidence failed, falling back: {exc}")
        self._sqlite.insert_evidence(record)

    def insert_claim(self, record: dict) -> None:
        if self.active == "bigquery":
            try:
                self.bq.insert_rows("claims", [record])
                return
            except Exception as exc:
                logger.warning(f"BQ insert_claim failed, falling back: {exc}")
        self._sqlite.insert_claim(record)

    # ── Meta ──────────────────────────────────────────────────────────────────

    def entity_count(self) -> int:
        if self.active == "bigquery":
            try:
                rows = self.bq.query(
                    f"SELECT COUNT(*) as n FROM `{self.bq.project}.{self.bq.dataset}.entities`"
                )
                return rows[0]["n"] if rows else 0
            except Exception:
                pass
        return self._sqlite.entity_count()

    def claim_count(self) -> int:
        if self.active == "bigquery":
            try:
                rows = self.bq.query(
                    f"SELECT COUNT(*) as n FROM `{self.bq.project}.{self.bq.dataset}.transmission_chains`"
                )
                return rows[0]["n"] if rows else 0
            except Exception:
                pass
        return self._sqlite.claim_count()


_router_instance: Optional[DBRouter] = None


def get_db_router() -> DBRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = DBRouter()
    return _router_instance
