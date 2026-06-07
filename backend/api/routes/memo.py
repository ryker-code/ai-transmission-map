import logging
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.api.schemas import MemoRequest, MemoResponse
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory memo store for PDF generation
_memo_store: dict = {}


@router.post("/generate", response_model=MemoResponse)
async def generate_memo(payload: MemoRequest):
    """
    Generate an investor-style memo from a thesis run using Claude claude-opus-4-5.
    Looks up the thesis run by ID from the shared run cache, then invokes the memo agent.
    """
    from backend.agents.memo_agent import generate_memo as _generate
    from backend.db.run_cache import get as get_run

    run_data = get_run(payload.thesis_run_id) or {}

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
    exposed_entities = run_data.get("exposed_entities", [
        "GE Vernova", "Vertiv Holdings", "Constellation Energy", "NextEra Energy",
    ])
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

    memo_id = str(uuid.uuid4())
    response = MemoResponse(
        memo_id=memo_id,
        memo_text=memo_text,
        regime=regime,
        key_bottlenecks=key_bottlenecks[:5],
        affected_names=exposed_entities[:6],
        model_used="claude-opus-4-5",
        created_at=datetime.now(timezone.utc),
    )
    _memo_store[memo_id] = {"memo": response.model_dump(), "thesis": thesis}
    return response


@router.post("/stream")
async def stream_memo(payload: MemoRequest):
    """
    Stream memo generation via Server-Sent Events.
    Client should use fetch() with ReadableStream (not EventSource, which is GET-only).
    Emits: data: {"chunk": "text", "tokens": N}  per token
    Final:  data: {"done": true, "memo_id": "...", "run_id": "..."}
    """
    from backend.agents.memo_agent import generate_memo_stream
    from backend.db.run_cache import get as get_run

    run_data = get_run(payload.thesis_run_id) or {}

    thesis = run_data.get("thesis", "AI infrastructure thesis")
    support_score = run_data.get("support_score", 0.72)
    contradiction_score = run_data.get("contradiction_score", 0.28)
    regime = run_data.get("regime", "AI_CAPEX_EXPANSION")
    key_bottlenecks = run_data.get("key_bottlenecks", [
        "Transformer Lead Times (80-120 week backlog)",
        "Grid Interconnection Queue (5+ year clearance)",
    ])
    exposed_entities = run_data.get("exposed_entities", ["GE Vernova", "Vertiv Holdings"])
    falsification_triggers = run_data.get("falsification_triggers", [
        "Transformer imports from Asia ramp faster than expected",
    ])

    return StreamingResponse(
        generate_memo_stream(
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
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/{memo_id}/pdf")
async def download_memo_pdf(memo_id: str):
    """Generate and stream a PDF of the investment memo identified by memo_id."""
    import io
    from backend.tools.pdf_export import generate_memo_pdf

    entry = _memo_store.get(memo_id)
    if entry is None:
        # Stub memo for demo when memo_id not in store
        entry = {
            "memo": {
                "memo_id": memo_id,
                "memo_text": "This memo was generated from a prior session and is no longer in memory. Re-generate via /memo/generate.",
                "regime": "AI_CAPEX_EXPANSION",
                "key_bottlenecks": ["Transformer Lead Times", "Grid Interconnection Queue"],
                "affected_names": ["GE Vernova", "Vertiv", "Constellation Energy"],
                "model_used": "claude-opus-4-5",
            },
            "thesis": "",
        }

    pdf_bytes = generate_memo_pdf(entry["memo"], entry.get("thesis", ""))
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="memo-{memo_id[:8]}.pdf"'},
    )
