# Interview Guide — AI Transmission Map

## 30-Second Pitch

"I built a multi-agent thesis interrogation tool for US AI infrastructure equity. You give it an investment thesis; it decomposes it into claims, scores each claim against 100+ entity nodes using a 5-component bottleneck algorithm, and generates a buyside LP memo with falsification triggers. The agent pipeline uses Claude Opus for deep reasoning and Gemini Flash for fast extraction — each node in the LangGraph workflow does one job."

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

**Q: Walk me through a bottleneck score of 58.5 for Hyperscaler GPU Clusters.**

A: evidence_intensity ≈ 0.70 (many inbound claims), × 0.30 = 0.21. Recency ≈ 0.65 (mix of 2023–2024 claims), × 0.20 = 0.13. Cross-source ≈ 0.75 (3+ distinct predicates), × 0.25 = 0.19. Market_confirmation = 0.50 (default), × 0.15 = 0.075. House_view_weight = 1.0 (no override), normalized × 0.10 = small contribution. Raw ≈ 0.70, normalized to ~58.5/100.

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
