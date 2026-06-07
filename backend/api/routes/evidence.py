import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from backend.api.schemas import EvidenceIngest, EvidenceResponse
from backend.auth import verify_api_key

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


@router.post("/", response_model=EvidenceResponse, dependencies=[Depends(verify_api_key)])
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
        # Invalidate stale caches after new evidence is ingested
        from backend.db.cache import get_cache
        cache = get_cache()
        cache.invalidate_prefix("graph:")
        cache.invalidate_prefix("bottlenecks:")
        cache.invalidate_prefix("regime:")
    except Exception as e:
        logger.error(f"Pipeline background task failed for note_id={note_id}: {e}")


@router.post("/image", response_model=dict, dependencies=[Depends(verify_api_key)])
async def ingest_image(
    image: UploadFile = File(...),
    analyst_context: str = Form(..., min_length=10),
    source_url: str = Form(""),
):
    """
    Extract transmission claims from a chart, slide, or diagram image.
    Uses Claude claude-opus-4-5 vision. Accepted formats: PNG, JPEG.
    Runs extracted claims through the critic → scorer pipeline.
    """
    allowed_types = {"image/png", "image/jpeg", "image/jpg"}
    if image.content_type not in allowed_types:
        return {"error": f"Unsupported file type: {image.content_type}. Use PNG or JPEG.", "claims": []}

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        return {"error": "Image too large (max 10 MB)", "claims": []}

    try:
        from backend.tools.image_intake import extract_claims_from_image
        from backend.agents.critic import run_critic, run_scorer

        raw_claims = await extract_claims_from_image(image_bytes, analyst_context, source_url or None)
        critiqued = run_critic(raw_claims, analyst_context)
        run_scorer(critiqued)

        accepted = [c for c in critiqued if c.get("status") != "rejected"]
        return {
            "status": "processed",
            "source_url": source_url,
            "analyst_context": analyst_context,
            "claims_extracted": len(raw_claims),
            "claims_accepted": len(accepted),
            "claims": accepted[:10],
        }
    except Exception as e:
        logger.error(f"Image ingest failed: {e}")
        return {"error": str(e), "claims": []}


@router.post("/voice", response_model=dict, dependencies=[Depends(verify_api_key)])
async def ingest_voice(
    audio: UploadFile = File(...),
    analyst_context: str = Form(..., min_length=10),
):
    """
    Transcribe an audio note via OpenAI Whisper, then extract transmission claims via Claude.
    Accepted formats: .mp3, .mp4, .wav, .m4a, .webm (max 25 MB).
    Runs extracted claims through the critic → scorer pipeline.
    """
    allowed_types = {
        "audio/mpeg", "audio/mp4", "audio/wav", "audio/x-wav",
        "audio/m4a", "audio/x-m4a", "audio/webm", "video/webm",
        "audio/ogg", "application/octet-stream",
    }
    allowed_exts = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg"}
    import os
    ext = os.path.splitext(audio.filename or "")[1].lower()
    if audio.content_type not in allowed_types and ext not in allowed_exts:
        return {"error": f"Unsupported format: {audio.content_type}. Use MP3, WAV, M4A, or WebM.", "claims": []}

    audio_bytes = await audio.read()
    if len(audio_bytes) > 25 * 1024 * 1024:
        return {"error": "Audio file too large (max 25 MB)", "claims": []}

    try:
        from backend.tools.voice_intake import transcribe_audio, extract_claims_from_transcript
        from backend.agents.critic import run_critic, run_scorer

        transcript = await transcribe_audio(audio_bytes, audio.filename or "audio.wav")
        raw_claims = await extract_claims_from_transcript(transcript, analyst_context)
        critiqued = run_critic(raw_claims, analyst_context)
        run_scorer(critiqued)

        accepted = [c for c in critiqued if c.get("status") != "rejected"]
        return {
            "status": "processed",
            "transcript": transcript[:500] + "..." if len(transcript) > 500 else transcript,
            "analyst_context": analyst_context,
            "claims_extracted": len(raw_claims),
            "claims_accepted": len(accepted),
            "claims": accepted[:10],
        }
    except Exception as e:
        logger.error(f"Voice ingest failed: {e}")
        return {"error": str(e), "claims": []}
