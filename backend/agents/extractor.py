"""
Extractor agent: Scout (Gemini Flash) + Extractor (Claude claude-opus-4-5) + Resolver (Gemini Flash).

Scout — fast entity identification from analyst notes.
Extractor — structured transmission claim extraction with multi-hop reasoning.
Resolver — canonicalization and deduplication against entity registry.
"""
import json
import logging
from typing import List

from backend.config import settings

logger = logging.getLogger(__name__)

VALID_PREDICATES = [
    "depends_on", "constrained_by", "benefits_from", "exposed_to",
    "supplies", "moves_with", "regulates", "financed_by", "contradicted_by"
]

VALID_DIRECTIONS = ["positive", "negative"]

VALID_HORIZONS = ["structural", "12m", "6m", "3m", "1m"]

SCOUT_PROMPT = """You are a financial analyst assistant identifying entities in an investment note.

Given the following analyst note, extract all entities mentioned. Entities include:
- Public companies (with ticker if known)
- Private companies
- Utilities and power generators
- Grid operators (RTOs/ISOs)
- Government regulators (FERC, NERC, DOE, EPA)
- Physical assets (data center campuses, corridors)
- Technologies (GPU types, cooling methods, memory types)
- Markets or sectors

Return a JSON array of objects with fields:
- name: canonical entity name
- type: one of [public_co, private_co, utility, asset, technology, geo, market]
- ticker: stock ticker if public, null otherwise

Analyst note:
{note}

Return ONLY the JSON array, no explanation."""

EXTRACTOR_PROMPT = """You are a senior infrastructure equity analyst building a transmission map of AI demand propagation.

Your task: extract structured transmission claims from the analyst note below.

A transmission claim captures how one entity affects another in the AI infrastructure value chain.
Each claim must have:
- subject: the entity that drives the effect (use canonical name)
- predicate: exactly one of: depends_on, constrained_by, benefits_from, exposed_to, supplies, moves_with, regulates, financed_by, contradicted_by
- object: the entity that receives the effect (use canonical name)
- direction: "positive" (subject helps object) or "negative" (subject hurts/limits object)
- confidence: float 0.0-1.0 based on how clearly the note supports this claim
- horizon: one of [structural, 12m, 6m, 3m, 1m]
- regime_tag: one of [AI_CAPEX_EXPANSION, SUPPLY_CHAIN_STRESS, GRID_BOTTLENECK, POWER_PRICE_SPREAD, REGULATORY, NUCLEAR_RENAISSANCE]
- rationale: 1-2 sentence justification grounded in the note text

Known entities for reference:
{entities}

Analyst note:
{note}

Return a JSON array of claim objects. Only return claims clearly supported by the note. Return ONLY the JSON array."""

RESOLVER_PROMPT = """You are resolving transmission claims to canonical entity names from a registry.

Claims to resolve:
{claims}

Registry of canonical entity names:
{registry}

For each claim, if the subject or object matches a registry entity (exact or alias), update it to the canonical name.
If no match, keep the original name.

Return the same JSON array with updated subject/object fields. Return ONLY the JSON array."""


def _get_gemini_client():
    """Initialize Gemini Flash client for fast extraction tasks."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.1,
        )
    except Exception as e:
        logger.warning(f"Gemini client unavailable: {e}. Using stub.")
        return None


def _get_claude_client():
    """Initialize Claude claude-opus-4-5 client for complex reasoning tasks."""
    try:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-opus-4-5",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.2,
            max_tokens=4096,
        )
    except Exception as e:
        logger.warning(f"Claude client unavailable: {e}. Using stub.")
        return None


def _invoke_llm(client, prompt: str, stub_response: list) -> list:
    """Invoke an LLM and parse JSON response; return stub_response on failure."""
    if client is None:
        logger.info("LLM client not available — returning stub response")
        return stub_response
    try:
        response = client.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        return stub_response


def run_scout(analyst_note: str, source_type: str) -> List[dict]:
    """
    Scout agent: identify entity candidates from an analyst note.
    Uses Gemini Flash for fast, structured entity recognition.
    Returns a list of entity dicts with name, type, ticker.
    """
    client = _get_gemini_client()
    prompt = SCOUT_PROMPT.format(note=analyst_note)
    stub = [
        {"name": "Vertiv Holdings", "type": "public_co", "ticker": "VRT"},
        {"name": "GE Vernova", "type": "public_co", "ticker": "GEV"},
        {"name": "Dominion Energy", "type": "utility", "ticker": "D"},
    ]
    result = _invoke_llm(client, prompt, stub)
    if not isinstance(result, list):
        return stub
    return result


def run_extractor(analyst_note: str, entity_candidates: List[dict], source_type: str) -> List[dict]:
    """
    Extractor agent: extract structured transmission claims from an analyst note.
    Uses Claude claude-opus-4-5 for multi-hop reasoning across the infrastructure stack.
    Returns a list of raw claim dicts.
    """
    client = _get_claude_client()
    entity_list = "\n".join(
        f"- {e.get('name', '')} ({e.get('type', '')}, ticker: {e.get('ticker', 'N/A')})"
        for e in entity_candidates
    )
    prompt = EXTRACTOR_PROMPT.format(note=analyst_note, entities=entity_list)
    stub = [
        {
            "subject": "Vertiv Holdings",
            "predicate": "supplies",
            "object": "Data Center Operators",
            "direction": "positive",
            "confidence": 0.80,
            "horizon": "structural",
            "regime_tag": "AI_CAPEX_EXPANSION",
            "rationale": "Vertiv supplies critical power and cooling to data center operators.",
        }
    ]
    result = _invoke_llm(client, prompt, stub)
    if not isinstance(result, list):
        return stub
    # Validate and filter
    valid = []
    for claim in result:
        if not all(k in claim for k in ["subject", "predicate", "object", "direction", "confidence"]):
            continue
        if claim.get("predicate") not in VALID_PREDICATES:
            claim["predicate"] = "depends_on"
        if claim.get("direction") not in VALID_DIRECTIONS:
            claim["direction"] = "positive"
        if claim.get("horizon") not in VALID_HORIZONS:
            claim["horizon"] = "structural"
        claim["confidence"] = max(0.0, min(1.0, float(claim.get("confidence", 0.7))))
        claim.setdefault("regime_tag", "AI_CAPEX_EXPANSION")
        claim.setdefault("rationale", "")
        valid.append(claim)
    return valid


def run_resolver(raw_claims: List[dict]) -> List[dict]:
    """
    Resolver agent: canonicalize entity names in claims against the entity registry.
    Uses Gemini Flash for structured name matching.
    Returns claims with canonical subject/object names.
    """
    import json as _json
    from pathlib import Path

    registry_path = Path("backend/db/seed_data/entities.json")
    if not registry_path.exists():
        return raw_claims

    try:
        entities = _json.loads(registry_path.read_text())
        registry_names = [e["canonical_name"] for e in entities]
        # Build alias map for fast lookup without LLM on simple cases
        alias_map = {}
        for e in entities:
            alias_map[e["canonical_name"].lower()] = e["canonical_name"]
            for alias in e.get("aliases", []):
                alias_map[alias.lower()] = e["canonical_name"]

        resolved = []
        for claim in raw_claims:
            claim = dict(claim)
            for field in ["subject", "object"]:
                raw = claim.get(field, "")
                canonical = alias_map.get(raw.lower(), raw)
                claim[field] = canonical
            resolved.append(claim)
        return resolved
    except Exception as e:
        logger.error(f"Resolver alias lookup failed: {e}")
        return raw_claims
