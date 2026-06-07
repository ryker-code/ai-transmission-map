# AI Infrastructure Transmission Map — Elevator Pitches

---

## 30-second version (recruiter screen)

"I built a multi-agent RAG system that maps AI infrastructure capacity constraints
as a transmission graph. It ingests evidence from URLs, images, and voice; extracts
causal claims via Gemini and Claude; scores bottleneck nodes using a 5-component
weighted algorithm; and lets analysts run 'what-if' scenario branches on investment
theses. 96 tests, 200 entities, live streaming memos. Built in 7 days."

---

## 2-minute version (hiring manager)

The AI infrastructure build-out has created a new class of investment problem: how
do you systematically track which supply chain constraints actually transmit to stock
prices — and how quickly? Traditional research is manual, siloed, and slow.

I built a multi-agent system that treats the infrastructure supply chain as a directed
graph. Agents ingest analyst notes, earnings transcripts, regulatory filings, and
charts; extract structured causal claims between entities (e.g., "transformer lead
times constrain grid interconnection for data center developers"); and score each
entity by how bottlenecked it is, based on 5 evidence-weighted components.

The key differentiators are three:

1. **Scenario branching** — an analyst can ask "what if FERC approves fast-track
   interconnection?" and the system spawns a parallel edge set, recomputes all
   bottleneck scores, and shows the delta vs. the base case — without touching the
   main graph.

2. **Multi-model attribution** — every extracted claim tracks which LLM produced it
   (Gemini Flash for scouting, Gemini 1.5 Pro for causal reasoning), so the analyst
   can calibrate how much to trust any given claim.

3. **Real-time streaming** — memo generation streams word-by-word via SSE. The
   analyst doesn't wait 30 seconds for a wall of text; they see the argument form in
   real time.

Technical choices: LangGraph for the state machine (explicit state transitions, easy
to debug vs. async spaghetti), BigQuery + SQLite dual-mode (runs locally without GCP
creds, scales to production), FastAPI with TTL cache on slow endpoints (p95 < 200ms
on cached bottleneck queries).

Build velocity: 0 to 96 tests, 14 pages, full agent pipeline in 6 days. Day 7 is
live deployment, E2E tests, and interview artifacts.

---

## 5-minute version (technical interview)

### The problem

Equity analysts covering AI infrastructure spend 30-40% of their time doing
transmission analysis manually: reading a transformer OEM earnings call, extracting
the claim that lead times are 80+ weeks, mapping that to the set of data center
developers who need new grid connections, and estimating the impact on their
construction timelines. There's no structured way to do this at scale.

### The architecture

The core is a LangGraph pipeline with 6 nodes:

```
Scout → Extractor → Resolver → Critic → Scorer → HouseView
```

**Scout** (Gemini Flash, fast) does entity identification from raw text — companies,
technologies, regulators, assets. This is deliberately cheap because most text has
low signal.

**Extractor** (Gemini 1.5 Pro) does structured claim extraction — a claim is a
`(subject, predicate, object, direction, confidence, regime_tag)` tuple. Predicates
are constrained to a vocabulary of 9: `depends_on`, `constrained_by`, `benefits_from`,
etc. This forces the model to produce graph-compatible output.

**Resolver** canonicalizes entity names against a 200-entity registry using fuzzy
matching and alias lookups. Without this, "NVDA" and "Nvidia Corporation" create two
disconnected nodes.

**Critic** does adversarial review — it checks claims against the existing claim set
for the same entity pair, adjusts confidence downward for low-specificity claims, and
rejects ones that are non-falsifiable.

**Scorer** computes a 5-component bottleneck score per entity:
- Evidence intensity (claim count, saturates at 5)
- Recency score (proxy: recent claim confidence)
- Cross-source agreement (multi-source confirmation)
- Market confirmation (price signal stub, wires to real data in v2)
- House view weight (analyst conviction override: 0.1x–3.0x)

### Key design decisions and tradeoffs

**LangGraph vs. vanilla async**: LangGraph gives explicit state transitions and a
debuggable checkpoint at every node. The tradeoff is overhead — for a 5-node pipeline
it's arguably overkill. The benefit is that adding a new agent (e.g., a "market signal
ingestion" node between Scorer and HouseView) is a 20-line change.

**BigQuery + SQLite dual-mode**: The DB router checks for a `BIGQUERY_PROJECT_ID` env
var at startup. If absent, it falls back to a SQLite file at `backend/db/local/`. This
means the entire demo runs without GCP credentials, which matters for recruiting demos
— no one wants to wait for IAM setup.

**Multi-model routing**: The routing table was initially Claude Opus + Gemini Flash.
I migrated to all-Gemini (Gemini 1.5 Pro for reasoning, Gemini Flash for extraction)
to eliminate paid API dependencies. The `ModelRouter` class makes this a 10-line
table change; every call logs which model ran it and the latency.

### What I'd do differently

1. **Entity resolution via vector search** — right now it's fuzzy string matching.
   A FAISS index over entity embeddings would handle acronyms and aliases much better,
   especially for private companies with multiple name variants.

2. **Real market signal feed** — the `market_confirmation` component is currently a
   proxy (confidence × 0.8). Wiring it to a real price/volume feed (even Yahoo Finance
   for demo purposes) would make the scorer reactive to earnings events.

3. **Claim deduplication** — the resolver prevents entity duplicates, but two claims
   with different phrasings but identical semantics both get stored. A semantic
   similarity filter on the claim store would reduce noise significantly.

### Known limitations with mitigation plans

1. **Evidence corpus is manually seeded** — there's no automated ingestion pipeline.
   Mitigation: an RSS feed watcher that polls SEC filings and earnings transcripts
   would run the pipeline continuously; this is a ~2-day addition.

2. **Scorer weights are heuristic** — the 5 component weights (0.30, 0.20, 0.20,
   0.15, 0.15) were calibrated by hand. A proper calibration against a labeled dataset
   of "high conviction calls that played out" would make the scorer empirically grounded.

3. **No real-time graph updates** — the graph is computed at request time from the
   claim store. For a live trading desk, you'd want a WebSocket connection pushing
   score deltas as new evidence arrives. The SSE streaming for memos is a proof of
   concept for this pattern.
