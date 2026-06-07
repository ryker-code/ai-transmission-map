"""Model router: maps task types to LLM models and logs every call."""
import json
import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_LOG_PATH = Path("backend/db/model_call_log.jsonl")


class ModelRouter:
    ROUTING_TABLE = {
        "entity_extraction": "gemini-2.0-flash",
        "causal_reasoning": "claude-opus-4-5",
        "critic_scoring": "claude-opus-4-5",
        "memo_generation": "claude-opus-4-5",
        "image_extraction": "claude-opus-4-5",
        "voice_transcription": "whisper-1",
        "structured_json": "gemini-2.0-flash",
        "house_view_narrative": "claude-opus-4-5",
    }

    def route(self, task_type: str) -> str:
        """Return model name for the given task type."""
        model = self.ROUTING_TABLE.get(task_type)
        if model is None:
            logger.warning(f"Unknown task_type '{task_type}', defaulting to claude-opus-4-5")
            return "claude-opus-4-5"
        return model

    def log_call(
        self,
        task_type: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        success: bool,
    ) -> None:
        """Append a call record to backend/db/model_call_log.jsonl."""
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": time.time(),
            "task_type": task_type,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "success": success,
        }
        try:
            with _LOG_PATH.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"model_router.log_call failed: {e}")

    def get_stats(self) -> dict:
        """Return per-model aggregated stats from the call log."""
        stats: dict[str, dict] = {}
        if not _LOG_PATH.exists():
            return {}
        try:
            lines = _LOG_PATH.read_text().splitlines()
            for line in lines:
                if not line.strip():
                    continue
                r = json.loads(line)
                m = r.get("model", "unknown")
                if m not in stats:
                    stats[m] = {
                        "call_count": 0,
                        "success_count": 0,
                        "total_latency_ms": 0,
                        "task_types": set(),
                    }
                stats[m]["call_count"] += 1
                if r.get("success"):
                    stats[m]["success_count"] += 1
                stats[m]["total_latency_ms"] += r.get("latency_ms", 0)
                stats[m]["task_types"].add(r.get("task_type", "unknown"))
        except Exception as e:
            logger.warning(f"model_router.get_stats failed: {e}")
            return {}
        result = {}
        for model, s in stats.items():
            count = s["call_count"]
            result[model] = {
                "call_count": count,
                "success_rate": round(s["success_count"] / count, 3) if count else 0.0,
                "avg_latency_ms": round(s["total_latency_ms"] / count) if count else 0,
                "task_types": sorted(s["task_types"]),
            }
        return result


_router = ModelRouter()


def get_router() -> ModelRouter:
    """Return the module-level singleton ModelRouter."""
    return _router
