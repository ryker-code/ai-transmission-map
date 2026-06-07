import logging
import uuid
from fastapi import APIRouter
from backend.api.schemas import MemoRequest, MemoResponse
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory thesis run cache for demo purposes
# In production this would query aitm.thesis_runs in BigQuery
_thesis_run_cache: dict = {}


def cache_thesis_run(run_id: str, run_data: dict):
    """Cache a thesis run result for memo generation."""
    _thesis_run_cache[run_id] = run_data


@router.post("/generate", response_model=MemoResponse)
async def generate_memo(payload: MemoRequest):
    """
    Generate an investor-style memo from a thesis run using Claude claude-opus-4-5.
    Looks up the thesis run by ID, then invokes the memo agent with style-specific prompting.
    """
    from backend.agents.memo_agent import generate_memo as _generate

    # Look up thesis run (from cache or use stub data)
    run_data = _thesis_run_cache.get(payload.thesis_run_id, {})

    thesis = run_data.get("thesis", "AI infrastructure thesis — transformer lead times and grid interconnection as primary bottlenecks")
    support_score = run_data.get("support_score", 0.72)
    contradiction_score = run_data.get("contradiction_score", 0.28)
    regime = run_data.get("regime", "AI_CAPEX_EXPANSION")
    key_bottlenecks = run_data.get("key_bottlenecks", [
        "Transformer Lead Times (80-120 week backlog)",
        "Grid Interconnection Queue (5+ year clearance)",
        "HBM Memory Supply (SK Hynix CoW yield constraints)",
        "Skilled Construction Labor (IBEW shortage in NoVA)",
    ])
    exposed_entities = run_data.get("exposed_entities", ["GE Vernova", "Vertiv Holdings", "Constellation Energy", "NextEra Energy"])
    falsification_triggers = run_data.get("falsification_triggers", [
        "Transformer imports from Asia ramp faster than expected",
        "FERC Order 2023 reforms accelerate queue clearing beyond base case",
        "HBM memory capacity additions outpace demand growth",
    ])

    memo_text = await _generate(
        thesis_run_id=payload.thesis_run_id,
        thesis=thesis,
        support_score=support_score,
        contradiction_score=contradiction_score,
        key_bottlenecks=key_bottlenecks,
        exposed_entities=exposed_entities,
        falsification_triggers=falsification_triggers,
        regime=regime,
        style=payload.style,
        max_words=payload.max_words,
    )

    return MemoResponse(
        memo_id=str(uuid.uuid4()),
        memo_text=memo_text,
        regime=regime,
        key_bottlenecks=key_bottlenecks[:5],
        affected_names=exposed_entities[:6],
        model_used="claude-opus-4-5",
        created_at=datetime.now(timezone.utc),
    )
