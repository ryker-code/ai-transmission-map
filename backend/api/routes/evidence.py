import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, Query
from backend.api.schemas import EvidenceIngest, EvidenceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/parse-url", response_model=dict)
async def parse_evidence_url(url: str = Query(..., description="bloomberg.com or public URL to parse")):
    """
    Parse a URL for metadata: title, tags, date, and any matched entity names.
    Used by the Evidence Ingest form to auto-fill fields before submission.
    """
    try:
        from backend.tools.bloomberg_parser import get_parser
        parser = get_parser()
        meta = parser.parse_url(url)
        entities = parser.extract_entities_from_title(meta["title"])
        return {**meta, "detected_entities": entities}
    except Exception as e:
        logger.error(f"parse-url failed: {e}")
        return {"title": "", "topic_tags": [], "source_type": "public",
                "estimated_date": None, "access_class": "metadata_only",
                "url": url, "detected_entities": [], "error": str(e)}


@router.post("/", response_model=EvidenceResponse)
async def ingest_evidence(payload: EvidenceIngest, background_tasks: BackgroundTasks):
    """
    Ingest a Bloomberg or public evidence note and trigger the full LangGraph pipeline.
    For bloomberg source_type, auto-enriches with URL metadata before pipeline runs.
    Pipeline: Scout → Extractor → Resolver → Critic → Scorer (async background task).
    Returns immediately with source_id and note_id; pipeline runs in background.
    """
    source_id = str(uuid.uuid4())
    note_id = str(uuid.uuid4())

    # Auto-enrich bloomberg sources with URL metadata
    enriched_title = payload.title
    enriched_tags = list(payload.tags)
    if payload.source_type == "bloomberg":
        try:
            from backend.tools.bloomberg_parser import get_parser
            parser = get_parser()
            meta = parser.parse_url(payload.url)
            if not enriched_title or enriched_title == payload.url:
                enriched_title = meta["title"]
            for tag in meta.get("topic_tags", []):
                if tag not in enriched_tags:
                    enriched_tags.append(tag)
        except Exception as e:
            logger.warning(f"Bloomberg enrichment failed for {payload.url}: {e}")

    background_tasks.add_task(
        _run_pipeline_background,
        source_id=source_id,
        note_id=note_id,
        payload=payload,
        enriched_title=enriched_title,
    )

    return EvidenceResponse(
        source_id=source_id,
        note_id=note_id,
        extracted_entities=[],
        claims_created=0,
        status="processing",
    )


async def _run_pipeline_background(source_id: str, note_id: str,
                                   payload: EvidenceIngest, enriched_title: str = ""):
    """Background task: run the full orchestrator pipeline for an evidence note."""
    try:
        from backend.agents.orchestrator import run_pipeline
        result = await run_pipeline(
            source_id=source_id,
            note_id=note_id,
            analyst_note=payload.analyst_note,
            source_type=payload.source_type,
            url=payload.url,
            title=enriched_title or payload.title,
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
