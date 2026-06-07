"""Score history: appends bottleneck scores with timestamp to score_history.jsonl."""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
_HISTORY_PATH = Path(__file__).parent / "local/score_history.jsonl"


def record_scores(scores: list) -> None:
    """Append a snapshot of bottleneck scores to the history file."""
    try:
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with _HISTORY_PATH.open("a") as f:
            for s in scores:
                entry = {
                    "ts": ts,
                    "entity_id": s.entity_id,
                    "entity_name": s.entity_name,
                    "score": round(s.score, 2),
                    "components": s.components,
                }
                f.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.warning(f"score_history: failed to write snapshot: {exc}")


def get_entity_history(entity_id: str, limit: int = 30) -> list[dict]:
    """Return the last N score snapshots for an entity."""
    if not _HISTORY_PATH.exists():
        return []
    try:
        entries = []
        with _HISTORY_PATH.open() as f:
            for line in f:
                try:
                    row = json.loads(line)
                    if row.get("entity_id") == entity_id:
                        entries.append(row)
                except json.JSONDecodeError:
                    continue
        return entries[-limit:]
    except Exception as exc:
        logger.warning(f"score_history: read error: {exc}")
        return []
