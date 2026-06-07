import logging
import uuid
from fastapi import APIRouter, BackgroundTasks
from backend.api.schemas import EvidenceIngest, EvidenceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=EvidenceResponse)
async def ingest_evidence(payload: EvidenceIngest, background_tasks: BackgroundTasks):
    """
    Ingest a Bloomberg or public evidence note and trigger the full LangGraph pipeline.
    Pipeline: Scout → Extractor → Resolver → Critic → Scorer (async background task).
    Returns immediately with source_id and note_id; pipeline runs in background.
    """
    source_id = str(uuid.uuid4())
    note_id = str(uuid.uuid4())

    background_tasks.add_task(
        _run_pipeline_background,
        source_id=source_id,
        note_id=note_id,
        payload=payload,
    )

    # Return optimistic response; background task fills in real entity/claim counts
    return EvidenceResponse(
        source_id=source_id,
        note_id=note_id,
        extracted_entities=[],
        claims_created=0,
        status="processing",
    )


async def _run_pipeline_background(source_id: str, note_id: str, payload: EvidenceIngest):
    """Background task: run the full orchestrator pipeline for an evidence note."""
    try:
        from backend.agents.orchestrator import run_pipeline
        result = await run_pipeline(
            source_id=source_id,
            note_id=note_id,
            analyst_note=payload.analyst_note,
            source_type=payload.source_type,
            url=payload.url,
            title=payload.title,
        )
        logger.info(
            f"Pipeline complete for note_id={note_id}: "
            f"{len(result.get('extracted_entities', []))} entities, "
            f"{result.get('claims_created', 0)} claims"
        )
        if result.get("error"):
            logger.warning(f"Pipeline completed with error: {result['error']}")
    except Exception as e:
        logger.error(f"Pipeline background task failed for note_id={note_id}: {e}")
