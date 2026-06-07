import json
import logging
from pathlib import Path
from fastapi import APIRouter, Query
from backend.api.schemas import GraphResponse, GraphNode, GraphEdge
from backend.db.cache import get_cache
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()
_cache = get_cache()


def _load_graph_from_seed() -> GraphResponse:
    """Load graph nodes and edges from seed JSON files (SQLite stub path)."""
    entities_path = Path(__file__).parent.parent.parent / "db/seed_data/entities.json"
    chains_path = Path(__file__).parent.parent.parent / "db/seed_data/transmission_chains.json"

    if not entities_path.exists() or not chains_path.exists():
        return GraphResponse(nodes=[], edges=[], regime_tag="AI_CAPEX_EXPANSION",
                             computed_at=datetime.now(timezone.utc))

    entities = json.loads(entities_path.read_text())
    chains = json.loads(chains_path.read_text())

    entity_map = {e["canonical_name"]: e["id"] for e in entities}

    try:
        from backend.agents.scorer import compute_bottleneck_scores
        score_map = {b.entity_id: b.score for b in compute_bottleneck_scores()}
    except Exception:
        score_map = {}

    nodes = [
        GraphNode(
            id=e["id"],
            label=e["canonical_name"],
            entity_type=e["entity_type"],
            sector=e.get("sector"),
            bottleneck_score=score_map.get(e["id"]),
        )
        for e in entities
    ]

    edges = []
    for chain in chains:
        src_id = entity_map.get(chain["subject"])
        tgt_id = entity_map.get(chain["object"])
        if src_id and tgt_id:
            edges.append(GraphEdge(
                source=src_id,
                target=tgt_id,
                predicate=chain["predicate"],
                direction=chain["direction"],
                confidence=chain["confidence"],
                horizon=chain["horizon"],
            ))

    # Determine dominant regime tag
    regime_counts: dict = {}
    for chain in chains:
        tag = chain.get("regime_tag", "AI_CAPEX_EXPANSION")
        regime_counts[tag] = regime_counts.get(tag, 0) + 1
    dominant_regime = max(regime_counts, key=regime_counts.get) if regime_counts else "AI_CAPEX_EXPANSION"

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        regime_tag=dominant_regime,
        computed_at=datetime.now(timezone.utc),
    )


@router.get("/", response_model=GraphResponse)
async def get_graph(regime: str = Query(None, description="Filter by regime tag")):
    """Return the transmission graph with nodes and edges from the seed data store."""
    cache_key = f"graph:{regime or 'all'}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        graph = _load_graph_from_seed()
        if regime:
            # Filter edges to only those matching the regime
            # (nodes are always returned in full for context)
            chains_path = Path(__file__).parent.parent.parent / "db/seed_data/transmission_chains.json"
            if chains_path.exists():
                chains = json.loads(chains_path.read_text())
                entities_path = Path(__file__).parent.parent.parent / "db/seed_data/entities.json"
                entities = json.loads(entities_path.read_text())
                entity_map = {e["canonical_name"]: e["id"] for e in entities}
                filtered_edges = [
                    GraphEdge(
                        source=entity_map.get(c["subject"], c["subject"]),
                        target=entity_map.get(c["object"], c["object"]),
                        predicate=c["predicate"],
                        direction=c["direction"],
                        confidence=c["confidence"],
                        horizon=c["horizon"],
                    )
                    for c in chains
                    if c.get("regime_tag") == regime and entity_map.get(c["subject"]) and entity_map.get(c["object"])
                ]
                graph = GraphResponse(
                    nodes=graph.nodes,
                    edges=filtered_edges,
                    regime_tag=regime,
                    computed_at=datetime.now(timezone.utc),
                )
        _cache.set(cache_key, graph, ttl_seconds=60)
        return graph
    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        return GraphResponse(nodes=[], edges=[], regime_tag="AI_CAPEX_EXPANSION",
                             computed_at=datetime.now(timezone.utc))
