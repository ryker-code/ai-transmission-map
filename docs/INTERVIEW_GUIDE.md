# Interview Guide — AI Transmission Map

## 30-Second Pitch

"I built a multi-agent thesis interrogation tool for US AI infrastructure equity. You give it an investment thesis; it decomposes it into claims, scores each claim against 100+ entity nodes using a 5-component bottleneck algorithm, and generates a buyside LP memo with falsification triggers. The agent pipeline uses Claude Opus for deep reasoning and Gemini Flash for fast extraction — each node in the LangGraph workflow does one job."

---

## Day 5 Additions (Most Interview-Ready)

### A. Scenario Branching ("What If?" Workspace)
The most impressive live demo moment. After a thesis run completes, the analyst can click one of three pre-built scenario buttons:
- "Transformer lead times normalize (52 weeks)" — reduces confidence on transformer claims
- "FERC fast-track interconnection approved" — shifts grid interconnect confidence
- "Hyperscaler capex pause (−30%)" — reduces GPU demand confidence

Each calls `POST /thesis/scenario` with claim confidence overrides and returns a delta comparison (base → scenario) with a Claude narrative on investment implications. The side-by-side comparison shows support/contradiction score movement in basis points.

**File**: `backend/api/routes/thesis.py:run_scenario()`

### B. Model Attribution
Every LLM call is routed through `ModelRouter` and logged to `backend/db/model_call_log.jsonl`. The `/models/status` endpoint returns per-model call counts, avg latency, and success rates. Claim cards show an `extracted_by` badge (e.g., "claude-opus-4-5"). The Models page auto-refreshes every 30s.

**File**: `backend/tools/model_router.py`

### C. Market Signals (Stub → Production-Ready)
Market confirmation score now reads from `MarketSignals.mock_data` (25 tickers) instead of a hardcoded 0.5. The entity detail page shows a momentum pill, rel_perf_30d badge, and vol percentile bar. Clear `TODO` markers show exactly where to wire in Alpha Vantage / yfinance.

**File**: `backend/tools/market_signals.py`

---

## Five Technical Highlights

### 1. Bottleneck Scoring Algorithm
Five-component weighted formula, normalized 0–100:

```
score = evidence_intensity(0.30) + recency_decay(0.20)
      + cross_source_agreement(0.25) + market_confirmation(0.15)
      + house_view_weight(0.10)
```

- Recency: `e^(-days/30)` decay — 30-day half-life
- Cross-source: proxy via distinct predicates per entity
- House view: analyst conviction adjusts ±10 pts on 0–100 scale
- MAX_RAW = 1.20; normalized to 100

**File**: `backend/agents/scorer.py`

### 2. LangGraph Pipeline Architecture
Five-node StateGraph: Scout → Extractor → Resolver → Critic → Scorer

- Scout (Gemini Flash): fast entity detection from raw text
- Extractor (Claude Opus): structured claim extraction with SPO triples
- Resolver: alias deduplication via EntityResolver singleton
- Critic: validates against seed transmission chains, rejects low-confidence claims
- Scorer: updates bottleneck scores with new runtime claims

**Why LangGraph?** Deterministic node ordering + typed state prevents the "prompt soup" failure mode of raw chain-of-thought agents.

### 3. Entity Resolver — Singleton Alias Index
Builds normalized alias index from seed data on first call, returns cached singleton on subsequent calls. Handles tickers, partial names, and multi-word sliding window extraction from text.

```python
resolver.resolve("GEV")      # → GE Vernova
resolver.resolve("Nvidia")   # → Nvidia
resolver.resolve("Constellation")  # → Constellation Energy
```

**File**: `backend/agents/resolver.py`

### 4. Multimodal Evidence Intake
Three intake pathways beyond text:
- **Bloomberg URL**: metadata extraction without HTTP (ToS-compliant)
- **Image**: Claude Opus vision on base64-encoded PNG/JPEG
- **Voice**: OpenAI Whisper transcription → Claude Opus claim extraction

All three flow through the same Critic → Scorer pipeline; runtime claims update regime detection in real time.

### 5. Regime Detection — Confidence-Weighted
Five regimes: AI_CAPEX_EXPANSION, SUPPLY_CHAIN_STRESS, GRID_BOTTLENECK, POWER_PRICE_SPREAD, REGULATORY.

Dominant regime = argmax of confidence-weighted claim tag distribution. New evidence shifts the regime immediately — no batch refresh required.

**File**: `backend/tools/regime_detector.py`

---

## Three Hard Engineering Questions

**Q: "Why not just use a vector DB for the claims?"**

A: Vector similarity retrieves claims *semantically close* to a query — not claims that *corroborate*
a thesis with distinct evidence. Ten Bloomberg articles about the same transformer backlog event score
identically high on vector similarity, but they represent one data point, not ten. The 5-component
scorer's `cross_source_agreement` component measures predicate diversity across entities, explicitly
penalizing this. Vector DBs are optimal for document retrieval; the bottleneck scorer is a structured
evidence aggregation problem where corroboration quality matters more than semantic closeness.

**Q: "How does the scorer handle conflicting evidence?"**

A: The Critic node rejects claims below confidence 0.5. For claims that pass Critic, conflicting
evidence (bullish + bearish predicates on the same entity) *reduces* the `cross_source_agreement`
score — not because we detect contradiction explicitly, but because predicate diversity decreases
when half the claims point in the same direction. The house view layer lets the analyst express
conviction when they have edge-case knowledge the model can't capture from the claim graph alone.

**Q: "What would you change if you had 6 months instead of 6 days?"**

A: Three things: (1) Real market data — Alpha Vantage/Polygon.io replacing the 25-ticker mock
(`backend/tools/market_signals.py` has exact `TODO` integration points). (2) Score history —
every scorer run writes to BigQuery time series; entity detail page shows 90-day sparkline.
(3) Multi-analyst collaboration — house view and watchlist scoped per-user via JWT. The interface
in `house_view_store.py` and `watchlist_store.py` already has the right shape; they just need a
`user_id` partition key and a BigQuery backend instead of the in-memory dict.

## Common Interview Questions

**Q: How does the house view interact with the LangGraph pipeline?**

A: House view is a separate store (`house_view_store.py`) that the scorer reads as a weight component. It doesn't modify the graph — it overlays a conviction multiplier (0.1–3.0×) that shifts bottleneck scores ±10 pts. This keeps the agent pipeline deterministic while allowing analyst overrides without re-running extraction.

**Q: Why BigQuery with a SQLite stub?**

A: BigQuery is the production target for claim persistence and regime history. The SQLite stub (`aitm_stub.db`) means the system runs fully offline in interviews — no GCP credentials required. The `USE_BIGQUERY` env flag switches between them. House view overrides persist to SQLite for session durability.

**Q: How do you prevent hallucinated claims from affecting scores?**

A: Three gates:
1. Critic node validates SPO triples against known entity names and seed chain predicates
2. Claims below confidence 0.5 are rejected
3. Cross-source agreement component in the scorer penalizes single-source claims — a hallucinated claim with no corroboration scores low on the 0.25-weight component

**Q: What's the falsification trigger mechanism?**

A: The thesis agent identifies 3–5 conditions that would invalidate the bull case (e.g., "transformer imports from Asia ramp >30% YoY"). These are stored in the `ThesisRunResponse` and surfaced in the memo. The regime timeline would flag if incoming evidence shifts the dominant regime tag.

**Q: How does the scenario branching work under the hood?**

A: `POST /thesis/scenario` accepts a `base_run_id` plus a list of `ClaimOverride` objects (claim_id + confidence_override). The endpoint loads the full seed graph, applies confidence adjustments to matching chains, recomputes bull/bear claim ratios, and returns delta_support and delta_contradiction vs the base run. Claude generates a 2-sentence narrative on the investment implication. The whole operation is stateless — scenarios don't mutate the main graph.

**Q: Walk me through a bottleneck score of 58.5 for Hyperscaler GPU Clusters.**

A: evidence_intensity ≈ 0.70 (many inbound claims), × 0.30 = 0.21. Recency ≈ 0.65 (mix of 2023–2024 claims), × 0.20 = 0.13. Cross-source ≈ 0.75 (3+ distinct predicates), × 0.25 = 0.19. Market_confirmation = 0.50 (default), × 0.15 = 0.075. House_view_weight = 1.0 (no override), normalized × 0.10 = small contribution. Raw ≈ 0.70, normalized to ~58.5/100.

---

## Day 6 Additions (Final Polish)

### D. BigQuery/SQLite Dual-Mode DB Router
`DBRouter` auto-detects credentials at startup. If BigQuery is unavailable (Codespace, no GCP creds),
all reads fall back to seed JSON files and writes go to `aitm_stub.db`. Swap `GOOGLE_CLOUD_PROJECT`
to a real project and the full 200-entity graph moves to BigQuery with zero code change.

**File**: `backend/db/db_router.py`, `backend/db/bq_client.py`

### E. API Key Auth + Rate Limiting
All write endpoints (`POST`, `PUT`, `DELETE`) require `X-Api-Key` header matching `AITM_API_KEY` env var.
Rate limits: `POST /evidence/` → 10/min, `POST /thesis/run` → 30/min, image/voice → 5/min.
`slowapi` handles limiting; `backend/auth.py` handles key validation.

### F. Weekly Digest Generator
`POST /digest/generate` aggregates regime, top score movers, house view calls, and falsification
alerts into a 400-word LP-style email. Claude claude-opus-4-5 formats it when the API key is configured;
a structured stub runs offline. See `docs/sample_digest.md` for a live example.

**File**: `backend/tools/digest_generator.py`, `backend/api/routes/digest.py`

### G. Architecture Deep Dive
`docs/ARCHITECTURE_DEEP_DIVE.md` covers: why LangGraph vs raw chains, why BigQuery vs Neo4j/Postgres,
5-component scorer weight rationale, why house view is a separate layer, TTL cache vs Redis,
multi-model routing cost/accuracy tradeoffs, and what changes in a production v2.

---

## Running the Demo (3 minutes)

```bash
# Terminal 1: Backend
cd backend && uvicorn main:app --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Demo script
python -m backend.scripts.demo_run

# API verification
curl http://localhost:8000/bottlenecks/?limit=5 | jq '.[].entity_name'
curl http://localhost:8000/regime/
```

**Demo thesis** (paste into `/thesis`):
> "Transformer manufacturing and grid interconnection are the binding constraints on US AI data center buildout through 2026, making GE Vernova and Constellation Energy the highest-conviction plays in the AI infrastructure stack."

Expected: support_score > 0.70, 3+ supporting claims, GEV and CEG in exposed_entities, falsification triggers about Asian transformer imports and FERC 2023.

---

## Architecture Diagram (text)

```
Analyst Thesis
      │
      ▼
LangGraph Pipeline
  Scout (Gemini Flash)     ← fast entity detection
  Extractor (Claude Opus)  ← SPO triple extraction
  Resolver                 ← alias deduplication
  Critic                   ← validation against seed graph
  Scorer                   ← 5-component bottleneck update
      │
      ▼
ThesisRunResponse
  ├── supporting_claims
  ├── contradicting_claims
  ├── exposed_entities
  ├── falsification_triggers
  └── graph_slice (filtered)
      │
      ▼
Memo Agent (Claude Opus)
  └── PDF Export (reportlab)
```

**Data stores**:
- Seed graph: `backend/db/seed_data/` (100 entities, 30+ chains)
- Runtime claims: `claims_store.py` in-memory
- House view: `house_view_store.py` + SQLite
- Run cache: `run_cache.py` (thesis→memo wiring)
