from fastapi import APIRouter
from backend.api.schemas import MemoRequest, MemoResponse
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/generate", response_model=MemoResponse)
async def generate_memo(payload: MemoRequest):
    """Generate an investor-style memo from a thesis run."""
    # TODO: Replace with real memo agent
    return MemoResponse(
        memo_id=str(uuid.uuid4()),
        memo_text="[Memo generation not yet implemented — Day 2 task]",
        regime="AI_CAPEX_EXPANSION",
        key_bottlenecks=["Transformer Lead Times", "Grid Interconnection Queue"],
        affected_names=["GE Vernova", "Vertiv", "Constellation Energy"],
        model_used="stub",
        created_at=datetime.utcnow()
    )
