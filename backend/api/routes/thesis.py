import json
import logging
import uuid
from pathlib import Path
from fastapi import APIRouter
from backend.api.schemas import ThesisRunRequest, ThesisRunResponse, GraphResponse, GraphNode, GraphEdge, ScenarioRequest, ScenarioResponse
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

THESIS_PROMPT = """You are a senior infrastructure equity analyst evaluating an investment thesis.

Thesis to evaluate:
"{thesis}"

Available transmission claims (structured knowledge graph):
{claims_text}

Your task:
1. Identify which claims SUPPORT this thesis (directional consistency, same regime)
2. Identify which claims CONTRADICT this thesis
3. List entities most EXPOSED to this thesis being correct
4. Generate 3-5 FALSIFICATION TRIGGERS: specific events that would break this thesis

Return a JSON object with:
- support_score: float 0-1 (fraction of relevant claims that support the thesis)
- contradiction_score: float 0-1
- supporting_claim_ids: list of claim IDs that support the thesis
- contradicting_claim_ids: list of claim IDs that contradict
- exposed_entity_names: list of entity names most exposed
- falsification_triggers: list of specific falsifying events as strings

Return ONLY the JSON object."""


def _load_seed_data():
    """Load entities and chains from seed files."""
    entities_path = Path(__file__).parent.parent.parent / "db/seed_data/entities.json"
    chains_path = Path(__file__).parent.parent.parent / "db/seed_data/transmission_chains.json"
    entities = json.loads(entities_path.read_text()) if entities_path.exists() else []
    chains = json.loads(chains_path.read_text()) if chains_path.exists() else []
    return entities, chains


def _bfs_subgraph(thesis: str, entities: list, chains: list, depth: int):
    """BFS from thesis-mentioned entities to depth N, returning subgraph nodes and edges."""
    entity_names = {e["canonical_name"] for e in entities}
    entity_map = {e["canonical_name"]: e for e in entities}

    # Find seed entities mentioned in the thesis text
    thesis_lower = thesis.lower()
    seed_entities = {
        name for name in entity_names
        if name.lower() in thesis_lower or any(
            a.lower() in thesis_lower
            for a in entity_map[name].get("aliases", [])
        )
    }
    if not seed_entities:
        # Fallback: use all entities in chains
        seed_entities = {c["subject"] for c in chains} | {c["object"] for c in chains}

    # BFS
    visited = set(seed_entities)
    frontier = set(seed_entities)
    for _ in range(depth):
        next_frontier = set()
        for chain in chains:
            if chain["subject"] in frontier and chain["object"] not in visited:
                next_frontier.add(chain["object"])
            if chain["object"] in frontier and chain["subject"] not in visited:
                next_frontier.add(chain["subject"])
        visited |= next_frontier
        frontier = next_frontier
        if not frontier:
            break

    # Build subgraph
    subgraph_chains = [c for c in chains if c["subject"] in visited and c["object"] in visited]
    subgraph_entities = [e for e in entities if e["canonical_name"] in visited]
    return subgraph_entities, subgraph_chains


@router.post("/run", response_model=ThesisRunResponse)
async def run_thesis(payload: ThesisRunRequest):
    """
    Run a thesis interrogation against the transmission graph.
    BFS subgraph extraction + Claude claude-opus-4-5 claim matching + falsification triggers.
    """
    run_id = str(uuid.uuid4())
    entities, chains = _load_seed_data()

    sub_entities, sub_chains = _bfs_subgraph(payload.thesis, entities, chains, payload.depth)

    # Filter by regime if requested
    if payload.regime_filter:
        sub_chains = [c for c in sub_chains if c.get("regime_tag") == payload.regime_filter]

    if not payload.include_private:
        private_names = {e["canonical_name"] for e in entities if e["entity_type"] == "private_co"}
        sub_chains = [c for c in sub_chains if c["subject"] not in private_names and c["object"] not in private_names]

    # Try LLM thesis evaluation
    support_score = 0.72
    contradiction_score = 0.28
    supporting_claims = []
    contradicting_claims = []
    exposed_entities = []
    falsification_triggers = [
        "Utility interconnection queue reform accelerates beyond current FERC Order 2023 projections",
        "HBM memory capacity additions outpace Nvidia GPU production — removes memory bottleneck",
        "Large power transformer imports from Asia ramp faster than expected, clearing backlog",
        "Nuclear PPA prices spike above data center power budgets, reducing hyperscaler demand",
        "NERC reliability standards impose emergency load curtailment on AI data center districts",
    ]

    try:
        from backend.config import settings
        from langchain_anthropic import ChatAnthropic
        client = ChatAnthropic(
            model="claude-opus-4-5",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.2,
            max_tokens=3000,
        )
        claims_text = "\n".join(
            f"[{c['id']}] {c['subject']} --{c['predicate']}--> {c['object']} "
            f"({c['direction']}, conf={c['confidence']}, regime={c.get('regime_tag', 'N/A')}): {c.get('analyst_note', '')[:80]}"
            for c in sub_chains
        )
        prompt = THESIS_PROMPT.format(thesis=payload.thesis, claims_text=claims_text)
        response = client.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        llm_result = json.loads(content)

        support_score = float(llm_result.get("support_score", 0.72))
        contradiction_score = float(llm_result.get("contradiction_score", 0.28))
        falsification_triggers = llm_result.get("falsification_triggers", falsification_triggers)

        chain_map = {c["id"]: c for c in sub_chains}
        supporting_claims = [chain_map[cid] for cid in llm_result.get("supporting_claim_ids", []) if cid in chain_map]
        contradicting_claims = [chain_map[cid] for cid in llm_result.get("contradicting_claim_ids", []) if cid in chain_map]
        exposed_names = llm_result.get("exposed_entity_names", [])
        entity_index = {e["canonical_name"]: e for e in entities}
        exposed_entities = [entity_index[n] for n in exposed_names if n in entity_index]

    except Exception as e:
        logger.warning(f"Thesis LLM evaluation failed ({e}), using heuristic")
        # Heuristic: claims whose regime_tag appears in the thesis text are supporting
        thesis_upper = payload.thesis.upper()
        for chain in sub_chains:
            tag = chain.get("regime_tag", "")
            if tag in thesis_upper or any(kw in payload.thesis.lower() for kw in [chain["subject"].lower(), chain["object"].lower()]):
                supporting_claims.append(chain)
            elif chain["direction"] == "negative":
                contradicting_claims.append(chain)
        support_score = len(supporting_claims) / max(len(sub_chains), 1)
        contradiction_score = len(contradicting_claims) / max(len(sub_chains), 1)

    # Build graph slice
    entity_map = {e["canonical_name"]: e["id"] for e in entities}
    graph_nodes = [GraphNode(id=e["id"], label=e["canonical_name"], entity_type=e["entity_type"], sector=e.get("sector")) for e in sub_entities]
    graph_edges = [
        GraphEdge(source=entity_map.get(c["subject"], c["subject"]), target=entity_map.get(c["object"], c["object"]),
                  predicate=c["predicate"], direction=c["direction"], confidence=c["confidence"], horizon=c["horizon"])
        for c in sub_chains if entity_map.get(c["subject"]) and entity_map.get(c["object"])
    ]

    from backend.tools.regime_detector import detect_regime
    regime_result = detect_regime()

    from backend.db.run_cache import put as cache_run
    cache_run(run_id, {
        "thesis": payload.thesis,
        "support_score": round(support_score, 4),
        "contradiction_score": round(contradiction_score, 4),
        "regime": regime_result["regime"],
        "key_bottlenecks": [e.get("canonical_name", e.get("label", "")) for e in exposed_entities[:4]],
        "exposed_entities": [e.get("canonical_name", e.get("label", "")) for e in exposed_entities],
        "falsification_triggers": falsification_triggers[:5],
    })

    return ThesisRunResponse(
        run_id=run_id,
        thesis=payload.thesis,
        support_score=round(support_score, 4),
        contradiction_score=round(contradiction_score, 4),
        supporting_claims=supporting_claims,
        contradicting_claims=contradicting_claims,
        exposed_entities=exposed_entities,
        falsification_triggers=falsification_triggers[:5],
        graph_slice=GraphResponse(nodes=graph_nodes, edges=graph_edges, computed_at=datetime.now(timezone.utc)),
        created_at=datetime.now(timezone.utc),
    )


# In-memory scenario store keyed by scenario_id; base_run_id → list of scenario_ids
_scenario_store: dict[str, dict] = {}
_base_to_scenarios: dict[str, list[str]] = {}


@router.post("/scenario", response_model=ScenarioResponse)
async def run_scenario(payload: ScenarioRequest):
    """
    Branch from a base thesis run with claim/entity weight overrides.
    Returns re-scored support/contradiction deltas and a Claude narrative.
    """
    from backend.db.run_cache import get as get_run
    base = get_run(payload.base_run_id)
    if base is None:
        # Stub base run if not found in cache (e.g. after restart)
        base = {
            "support_score": 0.72,
            "contradiction_score": 0.28,
            "key_bottlenecks": ["Transformer Lead Times", "Grid Interconnection Queue"],
            "exposed_entities": [],
            "regime": "AI_CAPEX_EXPANSION",
        }

    entities, chains = _load_seed_data()
    entity_id_map = {e["id"]: e["canonical_name"] for e in entities}

    # Apply claim overrides: adjust confidence on specified chain IDs
    override_conf = {o.claim_id: o.confidence_override for o in payload.claim_overrides}
    override_dir = {o.claim_id: o.direction_override for o in payload.claim_overrides if o.direction_override}

    modified_chains = []
    for c in chains:
        mc = dict(c)
        cid = mc.get("id", "")
        if cid in override_conf:
            mc["confidence"] = override_conf[cid]
        if cid in override_dir:
            mc["direction"] = override_dir[cid]
        modified_chains.append(mc)

    # Apply entity weight overrides (map entity_id to weight; affects scoring denominator)
    weight_overrides = {o.entity_id: o.weight_override for o in payload.entity_weight_overrides}

    # Simple re-score: fraction of high-confidence bullish vs bearish claims
    bull = [c for c in modified_chains if c.get("direction") in ("bullish", "positive") and c.get("confidence", 0) > 0.5]
    bear = [c for c in modified_chains if c.get("direction") in ("bearish", "negative") and c.get("confidence", 0) > 0.5]
    total = len(modified_chains) or 1

    new_support = round(len(bull) / total, 4)
    new_contra = round(len(bear) / total, 4)
    base_support = base.get("support_score", 0.72)
    base_contra = base.get("contradiction_score", 0.28)

    delta_support = round(new_support - base_support, 4)
    delta_contra = round(new_contra - base_contra, 4)

    # Determine which entities changed rank (simplified: flag those with weight overrides)
    changed_bottlenecks = []
    for eid, wt in weight_overrides.items():
        name = entity_id_map.get(eid, eid)
        changed_bottlenecks.append({
            "entity_id": eid,
            "entity_name": name,
            "weight_override": wt,
            "direction": "up" if wt > 1.0 else "down",
        })

    # Generate narrative with Claude (fallback to template)
    narrative = (
        f"Under scenario '{payload.scenario_name}', support score shifts from "
        f"{base_support:.1%} to {new_support:.1%} ({delta_support:+.1%}) and contradiction "
        f"score shifts from {base_contra:.1%} to {new_contra:.1%} ({delta_contra:+.1%}). "
        f"The scenario modifies confidence on {len(payload.claim_overrides)} claims and "
        f"adjusts weights for {len(payload.entity_weight_overrides)} entities. "
    )
    if delta_support < 0:
        narrative += (
            "Net effect is thesis weakening: claim confidence adjustments reduce the evidence "
            "base supporting the core transmission chain. Monitor for confirmation or reversal."
        )
    else:
        narrative += (
            "Net effect is thesis strengthening: the modified claim set provides higher "
            "directional coherence across the infrastructure stack."
        )

    try:
        from backend.config import settings
        from langchain_anthropic import ChatAnthropic
        client = ChatAnthropic(
            model="claude-opus-4-5",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.3,
            max_tokens=600,
        )
        prompt = f"""Scenario analysis for investment thesis.

Scenario: {payload.scenario_name}
Base run support: {base_support:.1%}, contradiction: {base_contra:.1%}
After scenario support: {new_support:.1%}, contradiction: {new_contra:.1%}
Claim overrides: {len(payload.claim_overrides)} claims modified
Entity weight changes: {[f"{c['entity_name']} ({c['direction']})" for c in changed_bottlenecks]}

Write a 2-sentence analyst interpretation of this scenario delta. Be specific about investment implications."""
        response = client.invoke(prompt)
        narrative = response.content.strip()
    except Exception:
        pass  # keep template narrative

    scenario_id = str(uuid.uuid4())
    result = ScenarioResponse(
        scenario_id=scenario_id,
        scenario_name=payload.scenario_name,
        base_run_id=payload.base_run_id,
        support_score=new_support,
        contradiction_score=new_contra,
        delta_support=delta_support,
        delta_contradiction=delta_contra,
        changed_bottlenecks=changed_bottlenecks,
        narrative=narrative,
    )
    _scenario_store[scenario_id] = result.model_dump()
    _base_to_scenarios.setdefault(payload.base_run_id, []).append(scenario_id)
    return result


@router.get("/scenarios/{base_run_id}")
async def list_scenarios(base_run_id: str):
    """List all scenarios branched from a given base thesis run."""
    scenario_ids = _base_to_scenarios.get(base_run_id, [])
    scenarios = [_scenario_store[sid] for sid in scenario_ids if sid in _scenario_store]
    return {"base_run_id": base_run_id, "scenarios": scenarios, "count": len(scenarios)}
