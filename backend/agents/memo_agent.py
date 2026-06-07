"""
Memo agent: generates investor-style memos from thesis run results.
Uses Claude claude-opus-4-5 with style-specific prompts for buyside LP, sellside note, and internal brief formats.
"""
import json
import logging
import time
from typing import AsyncGenerator, Literal

from backend.config import settings
from backend.tools.model_router import get_router

logger = logging.getLogger(__name__)
_router = get_router()

BUYSIDE_LP_PROMPT = """You are a senior portfolio manager writing an LP-facing investment note.

Write a structured investment memo based on the following thesis analysis.
The memo should be suitable for sending to a sophisticated limited partner.
Tone: confident, evidence-grounded, acknowledges risks directly.

Format:
- EXECUTIVE SUMMARY (2-3 sentences)
- THESIS (1 paragraph)
- TRANSMISSION CHAIN ANALYSIS (bullet points, specific to the infrastructure stack)
- KEY BOTTLENECKS (3-5 bullets, quantified where possible)
- EXPOSED NAMES (specific companies with brief rationale)
- FALSIFICATION TRIGGERS (conditions that would break this thesis)
- CONVICTION: High / Medium / Low with brief justification

Max {max_words} words. Be specific. Avoid clichés.

Thesis: {thesis}
Support score: {support_score:.0%}
Contradiction score: {contradiction_score:.0%}
Key bottlenecks: {bottlenecks}
Exposed entities: {exposed_entities}
Falsification triggers: {falsification_triggers}
Regime: {regime}"""

SELLSIDE_NOTE_PROMPT = """You are a sell-side equity research analyst at a bulge-bracket bank.

Write a research note based on the following infrastructure thesis analysis.
Tone: analytical, specific, avoids regulatory language.

Format:
- HEADLINE (one punchy sentence summarizing the call)
- INVESTMENT THESIS (2 paragraphs)
- SUPPLY CHAIN TRANSMISSION (bottleneck-by-bottleneck analysis)
- STOCK IMPLICATIONS (specific ticker implications with direction)
- RISKS TO THE CALL (specific, not generic)
- BOTTOM LINE

Max {max_words} words.

Thesis: {thesis}
Support score: {support_score:.0%}
Key bottlenecks: {bottlenecks}
Exposed entities: {exposed_entities}
Falsification triggers: {falsification_triggers}
Regime: {regime}"""

INTERNAL_BRIEF_PROMPT = """You are writing an internal research brief for the investment committee.

Format:
- ONE-LINE THESIS
- EVIDENCE SUMMARY (what the graph shows)
- SCORING (support/contradiction breakdown)
- WATCHLIST (entities to monitor)
- ACTION ITEMS (specific next research steps)
- MONITOR CONDITIONS (what would trigger a position review)

Max {max_words} words. Bullet-point heavy. No fluff.

Thesis: {thesis}
Support score: {support_score:.0%}
Contradiction score: {contradiction_score:.0%}
Key bottlenecks: {bottlenecks}
Exposed entities: {exposed_entities}
Falsification triggers: {falsification_triggers}
Regime: {regime}"""

PROMPTS = {
    "buyside_lp": BUYSIDE_LP_PROMPT,
    "sellside_note": SELLSIDE_NOTE_PROMPT,
    "internal_brief": INTERNAL_BRIEF_PROMPT,
}


async def generate_memo(
    thesis_run_id: str,
    thesis: str,
    support_score: float,
    contradiction_score: float,
    key_bottlenecks: list,
    exposed_entities: list,
    falsification_triggers: list,
    regime: str,
    style: Literal["buyside_lp", "sellside_note", "internal_brief"],
    max_words: int,
) -> str:
    """
    Generate an investor-style memo using Claude claude-opus-4-5.
    Returns memo text as a string. Falls back to a stub memo if API unavailable.
    """
    prompt_template = PROMPTS.get(style, BUYSIDE_LP_PROMPT)

    bottlenecks_str = "\n".join(f"- {b}" for b in key_bottlenecks) if key_bottlenecks else "- No bottlenecks identified"
    entities_str = "\n".join(f"- {e}" for e in exposed_entities) if exposed_entities else "- None identified"
    triggers_str = "\n".join(f"- {t}" for t in falsification_triggers) if falsification_triggers else "- None identified"

    prompt = prompt_template.format(
        thesis=thesis,
        support_score=support_score,
        contradiction_score=contradiction_score,
        bottlenecks=bottlenecks_str,
        exposed_entities=entities_str,
        falsification_triggers=triggers_str,
        regime=regime,
        max_words=max_words,
    )

    try:
        from langchain_anthropic import ChatAnthropic
        model = _router.route("memo_generation")
        client = ChatAnthropic(
            model=model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.4,
            max_tokens=min(max_words * 2, 4096),
        )
        t0 = time.monotonic()
        response = client.invoke(prompt)
        latency_ms = int((time.monotonic() - t0) * 1000)
        content = response.content.strip()
        _router.log_call("memo_generation", model, len(prompt), len(content), latency_ms, True)
        return content
    except Exception as e:
        logger.warning(f"Memo LLM generation failed ({e}), returning stub")
        _router.log_call("memo_generation", _router.route("memo_generation"), 0, 0, 0, False)

    # Stub memo when API is unavailable
    return f"""[STUB MEMO — API key not configured]


THESIS: {thesis}

TRANSMISSION CHAIN SUMMARY:
The graph analysis shows a support score of {support_score:.0%} against {contradiction_score:.0%} contradiction.

KEY BOTTLENECKS:
{bottlenecks_str}

EXPOSED NAMES:
{entities_str}

FALSIFICATION TRIGGERS:
{triggers_str}

REGIME: {regime}

Configure ANTHROPIC_API_KEY in .env to enable full LLM memo generation via Claude claude-opus-4-5."""


async def generate_memo_stream(
    thesis_run_id: str,
    thesis: str,
    support_score: float,
    contradiction_score: float,
    key_bottlenecks: list,
    exposed_entities: list,
    falsification_triggers: list,
    regime: str,
    style: Literal["buyside_lp", "sellside_note", "internal_brief"],
    max_words: int,
) -> AsyncGenerator[str, None]:
    """
    Stream an investor-style memo using Claude streaming API.
    Yields SSE-formatted strings: 'data: {...}\\n\\n' per chunk, then a done event.
    Falls back to chunked stub text when API key is absent.
    """
    prompt_template = PROMPTS.get(style, BUYSIDE_LP_PROMPT)
    bottlenecks_str = "\n".join(f"- {b}" for b in key_bottlenecks) if key_bottlenecks else "- No bottlenecks identified"
    entities_str = "\n".join(f"- {e}" for e in exposed_entities) if exposed_entities else "- None identified"
    triggers_str = "\n".join(f"- {t}" for t in falsification_triggers) if falsification_triggers else "- None identified"

    prompt = prompt_template.format(
        thesis=thesis,
        support_score=support_score,
        contradiction_score=contradiction_score,
        bottlenecks=bottlenecks_str,
        exposed_entities=entities_str,
        falsification_triggers=triggers_str,
        regime=regime,
        max_words=max_words,
    )

    import uuid
    memo_id = str(uuid.uuid4())
    total_tokens = 0

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        if "placeholder" in settings.anthropic_api_key.lower():
            raise ValueError("placeholder key")

        async with client.messages.stream(
            model=_router.route("memo_generation"),
            max_tokens=min(max_words * 2, 4096),
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                total_tokens += 1
                yield f"data: {json.dumps({'chunk': text, 'tokens': total_tokens})}\n\n"

        yield f"data: {json.dumps({'done': True, 'memo_id': memo_id, 'run_id': thesis_run_id, 'tokens': total_tokens})}\n\n"
        return

    except Exception as exc:
        logger.warning(f"Streaming memo LLM failed ({exc}), streaming stub text")

    # Stream stub text word-by-word for visual effect
    stub = (
        f"[STUB MEMO — API key not configured]\n\nTHESIS: {thesis}\n\n"
        f"SUPPORT SCORE: {support_score:.0%}\n\nKEY BOTTLENECKS:\n{bottlenecks_str}\n\n"
        f"EXPOSED NAMES:\n{entities_str}\n\nFALSIFICATION TRIGGERS:\n{triggers_str}\n\n"
        f"REGIME: {regime}\n\nConfigure ANTHROPIC_API_KEY to enable full streaming generation."
    )
    import asyncio
    for word in stub.split(" "):
        total_tokens += 1
        yield f"data: {json.dumps({'chunk': word + ' ', 'tokens': total_tokens})}\n\n"
        await asyncio.sleep(0.02)

    yield f"data: {json.dumps({'done': True, 'memo_id': memo_id, 'run_id': thesis_run_id, 'tokens': total_tokens})}\n\n"
