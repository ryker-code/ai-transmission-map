"""
LangGraph orchestrator for the AI Transmission Map evidence ingestion pipeline.
State machine: Scout → Extractor → Resolver → Critic → Scorer
"""
import logging
from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """Shared state passed between all pipeline agents."""
    source_id: str
    note_id: str
    analyst_note: str
    source_type: str
    url: str
    title: str
    # Scout output
    entity_candidates: List[dict]
    # Extractor output
    raw_claims: List[dict]
    # Resolver output
    resolved_claims: List[dict]
    # Critic output
    critiqued_claims: List[dict]
    # Scorer output
    bottleneck_updates: List[dict]
    # Final
    extracted_entities: List[str]
    claims_created: int
    error: Optional[str]


def scout_node(state: PipelineState) -> PipelineState:
    """
    Scout agent: identify entities mentioned in the analyst note.
    Uses Gemini Flash for fast entity recognition.
    """
    from backend.agents.extractor import run_scout
    logger.info(f"Scout running for note_id={state['note_id']}")
    try:
        entity_candidates = run_scout(state["analyst_note"], state["source_type"])
        return {**state, "entity_candidates": entity_candidates}
    except Exception as e:
        logger.error(f"Scout failed: {e}")
        return {**state, "entity_candidates": [], "error": str(e)}


def extractor_node(state: PipelineState) -> PipelineState:
    """
    Extractor agent: extract structured transmission claims from analyst note.
    Uses Claude claude-opus-4-5 for complex multi-hop reasoning.
    """
    from backend.agents.extractor import run_extractor
    logger.info(f"Extractor running with {len(state['entity_candidates'])} candidates")
    try:
        raw_claims = run_extractor(
            state["analyst_note"],
            state["entity_candidates"],
            state["source_type"]
        )
        return {**state, "raw_claims": raw_claims}
    except Exception as e:
        logger.error(f"Extractor failed: {e}")
        return {**state, "raw_claims": [], "error": str(e)}


def resolver_node(state: PipelineState) -> PipelineState:
    """
    Resolver agent: deduplicate and canonicalize claims against the entity registry.
    Uses Gemini Flash for structured output matching.
    """
    from backend.agents.extractor import run_resolver
    logger.info(f"Resolver running with {len(state['raw_claims'])} raw claims")
    try:
        resolved_claims = run_resolver(state["raw_claims"])
        return {**state, "resolved_claims": resolved_claims}
    except Exception as e:
        logger.error(f"Resolver failed: {e}")
        return {**state, "resolved_claims": state["raw_claims"], "error": str(e)}


def critic_node(state: PipelineState) -> PipelineState:
    """
    Critic agent: evaluate claim confidence and flag contradictions.
    Uses Claude claude-opus-4-5 for adversarial reasoning.
    """
    from backend.agents.critic import run_critic
    logger.info(f"Critic running with {len(state['resolved_claims'])} resolved claims")
    try:
        critiqued_claims = run_critic(state["resolved_claims"], state["analyst_note"])
        return {**state, "critiqued_claims": critiqued_claims}
    except Exception as e:
        logger.error(f"Critic failed: {e}")
        return {**state, "critiqued_claims": state["resolved_claims"], "error": str(e)}


def scorer_node(state: PipelineState) -> PipelineState:
    """
    Scorer agent: compute updated bottleneck scores for affected entities.
    Writes to BigQuery (or SQLite stub).
    """
    from backend.agents.critic import run_scorer
    logger.info(f"Scorer running with {len(state['critiqued_claims'])} critiqued claims")
    try:
        bottleneck_updates = run_scorer(state["critiqued_claims"])
        accepted = [c for c in state["critiqued_claims"] if c.get("status") != "rejected"]
        entity_names = list({c.get("subject", "") for c in accepted} | {c.get("object", "") for c in accepted})
        return {
            **state,
            "bottleneck_updates": bottleneck_updates,
            "extracted_entities": entity_names,
            "claims_created": len(accepted),
        }
    except Exception as e:
        logger.error(f"Scorer failed: {e}")
        return {**state, "bottleneck_updates": [], "claims_created": 0, "error": str(e)}


def build_pipeline() -> Any:
    """Build and compile the LangGraph evidence ingestion pipeline."""
    graph = StateGraph(PipelineState)

    graph.add_node("scout", scout_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("resolver", resolver_node)
    graph.add_node("critic", critic_node)
    graph.add_node("scorer", scorer_node)

    graph.set_entry_point("scout")
    graph.add_edge("scout", "extractor")
    graph.add_edge("extractor", "resolver")
    graph.add_edge("resolver", "critic")
    graph.add_edge("critic", "scorer")
    graph.add_edge("scorer", END)

    return graph.compile()


# Singleton compiled pipeline
_pipeline = None

def get_pipeline():
    """Return the compiled pipeline, building it on first call."""
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


async def run_pipeline(
    source_id: str,
    note_id: str,
    analyst_note: str,
    source_type: str,
    url: str,
    title: str,
) -> PipelineState:
    """
    Run the full ingestion pipeline for a single evidence note.
    Returns the final PipelineState with extracted_entities and claims_created.
    """
    pipeline = get_pipeline()
    initial_state: PipelineState = {
        "source_id": source_id,
        "note_id": note_id,
        "analyst_note": analyst_note,
        "source_type": source_type,
        "url": url,
        "title": title,
        "entity_candidates": [],
        "raw_claims": [],
        "resolved_claims": [],
        "critiqued_claims": [],
        "bottleneck_updates": [],
        "extracted_entities": [],
        "claims_created": 0,
        "error": None,
    }
    result = await pipeline.ainvoke(initial_state)
    return result
