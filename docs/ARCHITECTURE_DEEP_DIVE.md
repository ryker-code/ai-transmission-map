# Architecture Deep Dive — AI Transmission Map

A technical reference for engineering interviews. Covers design decisions, tradeoffs, and
what would change in a production v2.

---

## 1. Why LangGraph for the Agent Pipeline?

The pipeline runs five nodes: Scout → Extractor → Resolver → Critic → Scorer.

**The problem with raw chains:** Langchain chains execute linearly and accumulate context
without enforcing output schemas between steps. When Extractor returns a list of SPO triples,
a raw chain has no mechanism to validate structure before passing it to Resolver — bad extractions
corrupt downstream steps silently.

**Why LangGraph solves this:** Every node in LangGraph receives a typed `GraphState` dict and
returns a typed update. The state machine validates at every edge. If Critic rejects a claim, the
graph routes around Scorer for that claim — you don't write `if` blocks in a mega-function.

**The concrete tradeoff:** LangGraph adds ~50ms of overhead per pipeline invocation from state
serialization. For a thesis run, this is negligible. For a high-throughput streaming ingestion pipeline
(thousands of documents/hour), you'd replace LangGraph with a Kafka-backed worker queue and stateless
Python functions. We chose LangGraph because thesis runs happen at analyst speed (once per session),
not machine speed.

**Alternative considered:** Pure async FastAPI background tasks (no LangGraph). Rejected because
it provides no state visibility — debugging a broken pipeline at step 3 of 5 requires log archaeology.
LangGraph gives you a structured state dict at every node boundary.

---

## 2. Why BigQuery for the Graph Store?

The current design uses BigQuery as the production backend with a SQLite fallback for offline dev.

**Why not Neo4j?** The transmission graph is a DAG (directed acyclic graph), not a property graph
with arbitrary traversal patterns. Thesis interrogation is BFS over 2-3 hops from a seed entity set —
a pattern that SQL handles well with recursive CTEs. Neo4j's query model (Cypher) adds operational
complexity (managed service, separate auth, separate SDK) for a traversal pattern that BigQuery
handles natively. The only scenario where Neo4j wins is if you need variable-depth traversal with
complex relationship properties — not our case.

**Why not PostgreSQL?** Operational simplicity. BigQuery is serverless, scales to petabytes
without schema tuning, and the free tier (10GB storage, 1TB queries/month) covers demo usage at
zero marginal cost. A Postgres instance requires connection pooling, disk management, and vacuum
tuning as the claims table grows. BigQuery has none of these concerns.

**The SQLite fallback strategy:** `DBRouter` checks `BigQueryClient.available` on startup.
If credentials are absent or the project is a placeholder, all reads fall back to seed JSON files
and all writes go to `aitm_stub.db`. This means the full app — including bottleneck scoring, thesis
runs, and house view persistence — works offline in a GitHub Codespace with no external dependencies.

---

## 3. The 5-Component Scorer Design

```
score = evidence_intensity(0.30) + recency_decay(0.20)
      + cross_source_agreement(0.25) + market_confirmation(0.15)
      + house_view_weight(0.10)
```

**Why these weights?** The weights reflect information reliability hierarchy:
- `evidence_intensity` (0.30): Volume of claims pointing at an entity is the strongest raw signal.
  More inbound evidence = more analyst and market attention.
- `cross_source_agreement` (0.25): Corroboration across distinct predicates is a noise filter.
  Two Bloomberg articles about the same event count as one source — we measure predicate diversity,
  not article count.
- `recency_decay` (0.20): AI infrastructure supply chains move fast. A 2022 transformer backlog
  claim is less relevant than a 2024 claim; exponential decay with 30-day half-life.
- `market_confirmation` (0.15): Price action can lead or lag fundamental claims. We use it as a
  signal amplifier, not a primary driver — hence 0.15. A strong bull momentum ticker confirms a
  fundamental bottleneck claim; a bear signal may flag execution risk.
- `house_view_weight` (0.10): Analyst conviction is an overlay, not a driver. It adjusts ±10 pts
  on the 0–100 scale to express high/low conviction without overriding the evidence signal entirely.

**Why not just use a vector similarity score?** Vector search finds claims *similar* to a query,
not claims that *corroborate* a thesis with distinct evidence. Two near-identical Bloomberg headlines
about the same transformer backlog story score high on vector similarity but low on cross-source
agreement — vector search would overweight them. The 5-component scorer explicitly penalizes this
via the cross-source diversity component.

---

## 4. Why House View is a Separate Agent Layer

The house view applies *after* the LangGraph pipeline completes, not inside it. This is a deliberate
architectural choice.

**If house view were inside the pipeline:** Every thesis run would recompute with the current
analyst conviction, coupling the output to analyst state at run time. If an analyst changes their
conviction between two identical thesis runs, the results would differ — breaking reproducibility.

**Separate layer design:** `house_view_store.py` holds conviction multipliers (0.1–3.0×) that
the scorer reads as a static weight. `apply_house_view()` is called by the bottlenecks endpoint
after scoring completes. This means:
1. Thesis runs are deterministic given the same evidence graph.
2. Analyst can update conviction without re-running the full pipeline.
3. The house view store persists to SQLite — conviction calls survive server restarts.
4. In a multi-analyst environment, you can version house view states per-analyst without
   touching the underlying evidence graph.

---

## 5. TTL Cache Design — Why Not Redis?

The cache (`backend/db/cache.py`) is an in-process dict with monotonic TTL expiry.

**Why not Redis?** For a single-instance demo backend, a Redis cluster adds:
- Operational dependency: Redis server must be running, monitored, backed up
- Network latency: ~1ms per cache read vs ~0.01ms for in-process dict lookup
- Infrastructure cost: $15–30/month for a managed Redis instance

The in-process cache handles our access patterns:
- Graph data: 60s TTL, invalidated on evidence POST
- Bottleneck scores: 30s TTL, invalidated on house view PUT
- Model stats: 10s TTL, auto-expires

**When to switch to Redis:** Multi-instance horizontal scaling. Once you run 2+ backend replicas
behind a load balancer, in-process caches diverge — one instance serves stale data while another
has fresh data. Redis solves this with shared state across instances. At that point the operational
cost is justified.

**The invalidation design:** `invalidate_prefix()` evicts all keys matching a prefix string.
This lets evidence ingestion invalidate `graph:*` and `bottlenecks:*` in one call without knowing
every specific cache key. It's O(n) over cached keys but n is small (<100 in this application).

---

## 6. Multi-Model Routing Rationale

```python
ROUTING_TABLE = {
    "entity_extraction":    "gemini-2.0-flash",   # Fast, cheap, good at NER
    "causal_reasoning":     "claude-opus-4-5",     # Complex SPO triple extraction
    "critic_scoring":       "claude-opus-4-5",     # Adversarial validation
    "memo_generation":      "claude-opus-4-5",     # Long-form investor writing
    "image_extraction":     "claude-opus-4-5",     # Multimodal chart analysis
    "voice_transcription":  "whisper-1",           # Specialized ASR model
    "structured_json":      "gemini-2.0-flash",    # Fast structured output
}
```

**Cost vs accuracy tradeoff:**
- Scout (entity extraction from raw text): Gemini Flash handles this well at ~10× lower cost
  than Opus. It's a retrieval task, not a reasoning task.
- Extractor and Critic: Claude Opus handles causal chain construction and adversarial validation.
  These are reasoning tasks where output quality directly affects scoring correctness.
- Whisper: Purpose-built for ASR — using Claude for transcription would be both slower and
  less accurate.

**The `ModelRouter` logs every call** to `backend/db/model_call_log.jsonl` with token counts,
latency, and success rate. This enables cost attribution per pipeline step — in production,
you'd route this to a cost monitoring system (e.g., DataDog with custom metrics per model).

---

## 7. What Would Change in Production v2

| Area | Current (Demo) | Production v2 |
|------|----------------|---------------|
| DB routing | DBRouter → BigQuery/SQLite | DBRouter → BigQuery primary + read replica |
| Cache | In-process TTL dict | Redis cluster with pub/sub invalidation |
| Pipeline | LangGraph StateGraph | LangGraph + Kafka for async claim processing |
| Market data | 25-ticker mock (market_signals.py) | Alpha Vantage / Polygon.io live feed |
| Auth | Single shared API key | OAuth2 + per-analyst JWT tokens |
| Multi-analyst | Single store per entity | User-scoped house view versions |
| Graph updates | Batch recalculate on POST | Event-driven: claim insert → scorer update via queue |
| Streaming | SSE per memo request | WebSocket connection for real-time score updates |
| Deployment | Codespace / Railway single-instance | Cloud Run multi-region + Cloud Armor |
| Score history | Not persisted | `score_history.jsonl` → BigQuery time series |
| Alerts | None | Webhook / email when falsification trigger fires |

The six-day sprint demonstrated the full architecture in miniature. Each production gap has a clear
upgrade path that doesn't require rewriting the core domain logic.

---

## 8. Common Engineering Interview Questions

**Q: "Why not just use a vector DB for the claims?"**

A: Vector similarity finds claims *semantically close* to a query, not claims that *corroborate*
a thesis with distinct evidence. If I have 10 Bloomberg articles all describing the same transformer
backlog event, they score identically high on vector similarity to a "transformer bottleneck" query —
but they represent one data point, not ten. The 5-component scorer explicitly penalizes this via
`cross_source_agreement`, which measures predicate diversity, not claim count. Vector DBs are ideal
for document retrieval; the bottleneck scorer is a structured evidence aggregation problem.

**Q: "How does the scorer handle conflicting evidence?"**

A: The Critic node rejects claims below confidence 0.5 before they reach the Scorer. For claims
that pass Critic, the Scorer's `cross_source_agreement` component measures the diversity of
predicates per entity — so conflicting claims (bullish vs. bearish) actually *reduce* cross-source
agreement, which reduces the bottleneck score. An entity with 5 bullish claims and 1 bearish claim
scores differently than one with 3 bullish and 3 bearish. The house view layer lets an analyst
override this computation when they have edge-case knowledge the model can't capture.

**Q: "What would you change if you had 6 months instead of 6 days?"**

A: Three things: (1) Real market data feed — Alpha Vantage or Polygon.io replacing the 25-ticker
mock in `market_signals.py`. The integration points are already marked with `TODO` in the code.
(2) Score history persistence — every scorer run writes to a `score_history.jsonl` that feeds a
BigQuery time series. The entity detail page would show a 90-day score sparkline. (3) Multi-analyst
collaboration — house view and watchlist scoped per-user via JWT, with an analyst comparison view
showing where conviction diverges across the team. The in-memory stores in `house_view_store.py`
and `watchlist_store.py` already have the right interface; they just need a user_id partition key
and a Postgres or BigQuery backend.
