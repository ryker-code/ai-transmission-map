from fastapi import APIRouter
from backend.api.schemas import EvidenceIngest, EvidenceResponse
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/", response_model=EvidenceResponse)
async def ingest_evidence(payload: EvidenceIngest):
    """Ingest a Bloomberg or public evidence note and trigger claim extraction pipeline."""
    # TODO: Replace with real orchestrator call in Day 2
    return EvidenceResponse(
        source_id=str(uuid.uuid4()),
        note_id=str(uuid.uuid4()),
        extracted_entities=["Vertiv", "GE Vernova", "Dominion Energy"],
        claims_created=3,
        status="accepted"
    )
