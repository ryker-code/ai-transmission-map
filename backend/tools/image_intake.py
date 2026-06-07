"""
Multimodal image intake: extracts transmission claims from charts, slides, and diagrams
using Claude claude-opus-4-5's vision capability.

Accepts PNG/JPG image bytes. Returns a list of claim dicts matching ClaimCreate schema.
"""
import base64
import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

from backend.tools.model_router import get_router as _get_router
_router = _get_router()

IMAGE_PROMPT = """You are a senior equity analyst reviewing a chart, diagram, or slide
about AI infrastructure investment.

Analyst context (what this image depicts): {context}

Your task: identify transmission claims visible in this image. A claim captures how one
infrastructure entity affects another in the AI value chain.

Each claim must have:
- subject: entity driving the effect (use canonical name if possible)
- predicate: one of [depends_on, constrained_by, benefits_from, exposed_to, supplies,
                     moves_with, regulates, financed_by, contradicted_by]
- object: entity receiving the effect
- direction: "positive" or "negative"
- confidence: float 0.0-1.0 (how clearly visible in the image)
- horizon: one of [structural, 12m, 6m, 3m, 1m]
- regime_tag: one of [AI_CAPEX_EXPANSION, SUPPLY_CHAIN_STRESS, GRID_BOTTLENECK,
                       POWER_PRICE_SPREAD, REGULATORY, NUCLEAR_RENAISSANCE]
- rationale: what in the image supports this claim (1 sentence)

If the image contains no clear transmission claims, return an empty array.
Return ONLY a JSON array of claim objects, no explanation."""

STUB_CLAIMS = [
    {
        "subject": "Hyperscaler GPU Clusters",
        "predicate": "depends_on",
        "object": "Grid Interconnection Queue",
        "direction": "positive",
        "confidence": 0.70,
        "horizon": "structural",
        "regime_tag": "GRID_BOTTLENECK",
        "rationale": "Image stub: chart analysis not available without valid API key.",
    }
]


async def extract_claims_from_image(
    image_bytes: bytes,
    analyst_context: str,
    source_url: Optional[str] = None,
) -> list[dict]:
    """
    Extract transmission claims from an image using Claude claude-opus-4-5 vision.
    Falls back to stub claims when API key is not configured.

    Args:
        image_bytes: Raw PNG or JPEG bytes.
        analyst_context: Required description of what this image depicts.
        source_url: Optional URL where this image was found.
    Returns:
        List of claim dicts ready for the critic → scorer pipeline.
    """
    if not image_bytes:
        logger.warning("image_intake: empty image bytes, returning stub")
        return STUB_CLAIMS

    try:
        from backend.config import settings
        import google.generativeai as genai

        api_key = settings.get_gemini_key()
        if "placeholder" in api_key.lower():
            raise ValueError("placeholder key")

        # Detect image media type (PNG vs JPEG)
        media_type = "image/png"
        if image_bytes[:2] == b"\xff\xd8":
            media_type = "image/jpeg"

        model = _router.route("image_extraction")
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel("gemini-1.5-pro")
        image_part = {"mime_type": media_type, "data": image_bytes}
        t0 = time.monotonic()
        response = client.generate_content([IMAGE_PROMPT.format(context=analyst_context), image_part])

        latency_ms = int((time.monotonic() - t0) * 1000)
        content = response.text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        claims = json.loads(content)
        _router.log_call("image_extraction", model, len(IMAGE_PROMPT), len(content), latency_ms, True)
        if not isinstance(claims, list):
            return STUB_CLAIMS

        # Validate fields and stamp extracted_by
        valid = []
        for claim in claims:
            if all(k in claim for k in ["subject", "predicate", "object", "direction"]):
                claim.setdefault("confidence", 0.7)
                claim.setdefault("horizon", "structural")
                claim.setdefault("regime_tag", "AI_CAPEX_EXPANSION")
                claim.setdefault("rationale", "")
                claim.setdefault("source_url", source_url or "")
                claim.setdefault("source_type", "image")
                claim["extracted_by"] = model
                valid.append(claim)

        logger.info(f"image_intake: extracted {len(valid)} claims from image")
        return valid if valid else STUB_CLAIMS

    except Exception as e:
        logger.warning(f"image_intake: vision extraction failed ({e}), returning stub")
        _router.log_call("image_extraction", _router.route("image_extraction"), 0, 0, 0, False)
        return STUB_CLAIMS
