"""Weekly digest generation endpoint."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=dict, dependencies=[Depends(verify_api_key)])
async def generate_digest():
    """
    Generate a weekly summary digest from live stores.
    Uses Claude claude-opus-4-5 to format into a professional 400-word email-style digest.
    Falls back to a structured plaintext digest if API key is absent.
    """
    from backend.tools.digest_generator import generate_weekly_digest
    from backend.config import settings

    data = generate_weekly_digest()

    # Format via LLM or stub
    digest_text = ""
    try:
        import anthropic
        if "placeholder" in settings.anthropic_api_key.lower():
            raise ValueError("placeholder key")
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        movers_str = "\n".join(
            f"  - {m['entity']}: {m['prev_score']} → {m['curr_score']} ({'+' if m['delta']>0 else ''}{m['delta']}) — {m['reason']}"
            for m in data["top_score_movers"]
        ) or "  No score movers this week"

        alerts_str = "\n".join(f"  • {a}" for a in data["falsification_alerts"])
        calls_str = "\n".join(
            f"  - {c['entity']} ({c['conviction'].upper()}): {c['note']}"
            for c in data["analyst_calls"]
        )

        prompt = (
            f"You are a senior AI infrastructure equity analyst. Write a professional 400-word "
            f"weekly digest email for institutional LPs. Use the following data:\n\n"
            f"Week ending: {data['week_ending']}\n"
            f"Dominant regime: {data['dominant_regime']}\n"
            f"Regime changed: {data['regime_changed']}\n"
            f"Top bottleneck: {data['top_bottleneck']['entity']} (score: {data['top_bottleneck']['score']}, "
            f"key driver: {data['top_bottleneck']['key_driver']})\n"
            f"Score movers:\n{movers_str}\n"
            f"New evidence: {data['new_evidence_count']} notes, {data['new_claims_accepted']} claims accepted\n"
            f"Falsification alerts:\n{alerts_str}\n"
            f"Analyst calls:\n{calls_str}\n\n"
            f"Format: Subject line, then 4 sections with bold headers: "
            f"REGIME UPDATE, BOTTLENECK MOVEMENTS, ANALYST POSITIONING, WHAT TO WATCH. "
            f"Professional but readable. 400 words max. No bullet soup."
        )
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        digest_text = resp.content[0].text

    except Exception as exc:
        logger.warning(f"Digest LLM failed ({exc}), using stub formatter")
        movers = "\n".join(
            f"  • {m['entity']}: {m['prev_score']} → {m['curr_score']} ({'+' if m['delta']>0 else ''}{m['delta']} pts)"
            for m in data["top_score_movers"]
        ) or "  No notable score movements"

        digest_text = f"""Subject: AI Infrastructure Weekly Digest — Week of {data['week_ending']}

**REGIME UPDATE**
Current regime: {data['dominant_regime']}{'  ← CHANGED THIS WEEK' if data['regime_changed'] else ' (unchanged)'}
Top bottleneck: {data['top_bottleneck']['entity']} at {data['top_bottleneck']['score']}/100
Key driver: {data['top_bottleneck']['key_driver']}

**BOTTLENECK MOVEMENTS**
{movers}

New evidence ingested: {data['new_evidence_count']} notes, {data['new_claims_accepted']} claims accepted this week.

**ANALYST POSITIONING**
{data['house_view_summary']}

Active conviction calls:
""" + "\n".join(f"  • {c['entity']} ({c['conviction'].upper()}): {c['note']}" for c in data["analyst_calls"]) + f"""

**WHAT TO WATCH**
Falsification alerts (bearish signals this week):
""" + "\n".join(f"  • {a}" for a in data["falsification_alerts"]) + """

---
Configure ANTHROPIC_API_KEY to enable full LLM formatting via Claude claude-opus-4-5.
"""

    return {
        "digest_text": digest_text,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
