"""
Voice note intake: audio → Whisper transcription → Claude claim extraction.

Uses OpenAI Whisper API for transcription (falls back to stub if key is placeholder).
Extracted claims follow the same schema as image_intake.py.
"""
import io
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

STUB_TRANSCRIPT = (
    "Transformer lead times are now running over 100 weeks for large power transformers. "
    "GE Vernova and Hitachi Energy are both capacity constrained with backlogs extending "
    "into 2026. This is creating a bottleneck for data center developers in PJM territory "
    "who need grid interconnection. Constellation Energy benefits because they already have "
    "existing nuclear capacity with signed interconnection agreements."
)

VOICE_CLAIM_PROMPT = """You are analyzing a spoken analyst note about AI infrastructure investment.

Transcript:
{transcript}

Analyst context: {context}

Extract transmission claims between entities. Each claim must have:
- subject: entity driving the effect
- predicate: one of [depends_on, constrained_by, benefits_from, exposed_to, supplies,
                     moves_with, regulates, financed_by, contradicted_by]
- object: entity receiving the effect
- direction: "positive" or "negative"
- confidence: float 0.0-1.0
- horizon: one of [structural, 12m, 6m, 3m, 1m]
- regime_tag: one of [AI_CAPEX_EXPANSION, SUPPLY_CHAIN_STRESS, GRID_BOTTLENECK,
                       POWER_PRICE_SPREAD, REGULATORY, NUCLEAR_RENAISSANCE]
- rationale: 1 sentence from the transcript

Return ONLY a JSON array of claim objects."""


async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API.
    Falls back to stub transcript if API key is placeholder or unavailable.
    """
    if not audio_bytes:
        logger.warning("voice_intake: empty audio bytes")
        return STUB_TRANSCRIPT

    try:
        from backend.config import settings
        if "placeholder" in settings.openai_api_key:
            logger.info("voice_intake: OpenAI key is placeholder, using stub transcript")
            return STUB_TRANSCRIPT

        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
        logger.info(f"voice_intake: transcribed {len(audio_bytes)} bytes → {len(transcript)} chars")
        return str(transcript)

    except Exception as e:
        logger.warning(f"voice_intake: Whisper transcription failed ({e}), using stub")
        return STUB_TRANSCRIPT


async def extract_claims_from_transcript(transcript: str, analyst_context: str) -> list[dict]:
    """
    Extract structured transmission claims from a spoken analyst note transcript.
    Uses Claude claude-opus-4-5. Falls back to stub claims if API unavailable.
    """
    stub_claims = [
        {
            "subject": "Transformer Lead Times",
            "predicate": "constrained_by",
            "object": "Grid Interconnection Queue",
            "direction": "negative",
            "confidence": 0.85,
            "horizon": "structural",
            "regime_tag": "SUPPLY_CHAIN_STRESS",
            "rationale": "Transcript describes 100+ week lead times blocking interconnection.",
            "source_type": "voice",
        }
    ]

    try:
        from backend.config import settings
        from langchain_anthropic import ChatAnthropic

        client = ChatAnthropic(
            model="claude-opus-4-5",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.2,
            max_tokens=2048,
        )
        prompt = VOICE_CLAIM_PROMPT.format(transcript=transcript, context=analyst_context)
        response = client.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        claims = json.loads(content)
        if not isinstance(claims, list):
            return stub_claims
        for claim in claims:
            claim.setdefault("source_type", "voice")
        valid = [c for c in claims if all(k in c for k in ["subject", "predicate", "object", "direction"])]
        logger.info(f"voice_intake: extracted {len(valid)} claims from transcript")
        return valid if valid else stub_claims
    except Exception as e:
        logger.warning(f"voice_intake: claim extraction failed ({e}), returning stub")
        return stub_claims
