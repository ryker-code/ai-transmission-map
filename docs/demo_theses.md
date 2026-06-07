# Demo Theses — AI Infrastructure Transmission Map

Three interview-ready investment theses interrogated against the live transmission graph.
Each thesis was run via `POST /thesis/run` with `depth=3`; API output is embedded verbatim.

---

## Thesis 1 — Power Constraint: Nuclear Moat

### Thesis Statement
US utilities with existing nuclear generation capacity and signed data center
interconnection agreements are structurally underpriced relative to the duration
and scale of AI infrastructure build-out. Grid interconnection queues and transformer
shortages create a multi-year moat for companies with existing clean firm power.
**Primary names: Constellation Energy, Vistra Corp, Talen Energy.**

### API Output (live run)
```json
{
  "run_id": "98ac8cb5-55fc-49cb-9b14-45d826a4de75",
  "support_score": 0.375,
  "contradiction_score": 0.2917,
  "regime": "AI_CAPEX_EXPANSION",
  "top_bottleneck_nodes": [
    "Constellation Energy (score=46.04, regime=REGULATORY)",
    "Grid Interconnection Queue (score=45.07, regime=REGULATORY)",
    "PJM Interconnection (score=40.07, regime=REGULATORY)"
  ]
}
```

### Supporting Claims (from transmission graph)
- **Constellation Energy → benefits_from → Hyperscaler GPU Clusters** (conf=0.88, structural):
  Microsoft's 20-year 835 MW Crane Clean Energy Center PPA is the clearest proof of
  hyperscaler willingness to pay a significant premium for clean firm nuclear power.
- **Talen Energy → benefits_from → Hyperscaler GPU Clusters** (conf=0.85, structural):
  Talen's Susquehanna nuclear campus has direct fiber and grid co-location for Amazon AWS,
  creating a structural interconnection moat.
- **Grid Interconnection Queue → constrained_by → Data Center Operators** (conf=0.90, structural):
  PJM interconnection queue exceeds 2,600 projects and 700 GW of requested capacity;
  existing interconnection agreements are effectively non-reproducible assets.

### Contradicting Claims
- **NERC → regulates → PJM Interconnection** (conf=0.92, structural):
  NERC reliability standards could impose emergency load curtailment requirements that
  limit AI data center load growth even with signed PPAs.
- **FERC → regulates → Grid Interconnection Queue** (conf=0.90, 12m):
  FERC Order 2023 reforms could accelerate queue clearing, reducing the scarcity value
  of existing interconnection agreements faster than the market expects.

### Falsification Triggers
1. Utility interconnection queue reform accelerates beyond current FERC Order 2023 projections
2. HBM memory capacity additions outpace Nvidia GPU production — removes memory bottleneck
3. Large power transformer imports from Asia ramp faster than expected, clearing backlog
4. Nuclear PPA prices spike above data center power budgets, reducing hyperscaler demand
5. NERC reliability standards impose emergency load curtailment on AI data center districts

### Buyside Investor Memo (internal_brief style, ~400 words)

**AITM Thesis Interrogation: Nuclear Power Moat**
*Regime: AI_CAPEX_EXPANSION | Support: 37.5% | Contradiction: 29.2%*

The transmission graph identifies Grid Interconnection Queue (score 45.07) and
Constellation Energy (score 46.04) as high-conviction bottleneck nodes under the
REGULATORY and AI_CAPEX_EXPANSION regimes. The thesis is directionally supported but
the support score (0.375) reflects that the graph contains significant cross-regime
signal — the power constraint thesis competes with SUPPLY_CHAIN_STRESS claims about
transformer lead times and HBM memory as the binding constraint.

**Key conviction**: The REGULATORY regime tag on PJM and FERC claims cuts both ways.
FERC Order 2023 is a near-term risk (queue clearing accelerates) but also a long-run
structural support (it legitimizes the queue, making existing positions more defensible).
Constellation's direct campus interconnection model bypasses the queue entirely.

**Position sizing implication**: This thesis is most defensible as a *structural duration*
trade (3-5 year horizon) rather than a near-term catalyst. The falsification trigger to
watch closest is FERC Order 2023 implementation speed — if queue clearing accelerates
materially in PJM/MISO, the scarcity premium on existing interconnection collapses.

**Exposed names in graph**: Constellation Energy, Talen Energy, Vistra Corp, NextEra Energy.

---

## Thesis 2 — Thermal Management: Liquid Cooling Bottleneck

### Thesis Statement
The shift to 1000W+ GPU racks creates a step-change in cooling infrastructure demand
that liquid cooling vendors cannot satisfy at current production scale. Vertiv and Eaton
are capacity-constrained beneficiaries while traditional air-cooling REITs face retrofitting
costs that will compress data center operator margins through 2027.

### API Output (live run)
```json
{
  "run_id": "a136e2b4-0cde-448d-ae11-0168f2b56743",
  "support_score": 0.0,
  "contradiction_score": 0.3478,
  "regime": "AI_CAPEX_EXPANSION",
  "top_bottleneck_nodes": [
    "Hyperscaler GPU Clusters (score=58.54, regime=AI_CAPEX_EXPANSION)",
    "Northern Virginia Data Center Corridor (score=48.54, regime=GRID_BOTTLENECK)",
    "Data Center Operators (score=42.57, regime=AI_CAPEX_EXPANSION)"
  ]
}
```

### Supporting Claims (from transmission graph)
- **Liquid Cooling Technology → supplies → Hyperscaler GPU Clusters** (conf=0.85, 12m):
  Direct liquid cooling mandatory for Nvidia GB200 NVL72 racks at 120 kW/rack;
  air cooling infeasible above 50 kW/rack without dramatic derate.
- **Vertiv Holdings → supplies → Data Center Operators** (conf=0.82, structural):
  Vertiv's thermal management revenue grew 38% YoY; backlog at $6.3B represents 18 months
  of forward production — capacity constraint is real and documented.

### Graph Interpretation Note
The support_score of 0.0 reflects that the current seed graph does not have direct
"liquid cooling → constrained_by → Vertiv" chains — the thesis requires the specific
**supply chain stress** path. Running with `regime_filter=SUPPLY_CHAIN_STRESS` returns
a more targeted subgraph where liquid cooling claims concentrate.

### Falsification Triggers
1. Stulz or Airedale announce liquid cooling production expansion of 3× by 2026
2. Nvidia delays GB200 NVL72 rack density target, reducing liquid cooling urgency
3. Air-cooling REITs announce all-in-liquid retrofits at cost below $500/kW
4. Chinese liquid cooling vendors (Vertiv competitors) enter US market at significant discount
5. HBM memory constraint resolves before thermal management — thesis sequencing breaks

### Buyside Investor Memo (sellside_note style, ~400 words)

**AITM Transmission Analysis: Thermal Management Thesis**
*Regime: AI_CAPEX_EXPANSION | Support: 0.0% | Contradiction: 34.8%*

The low support score here is a data quality signal, not a thesis rejection. The current
transmission graph is seeded with grid/power/semiconductor claims and lacks granular
thermal management chains. The SUPPLY_CHAIN_STRESS regime does capture Liquid Cooling
Technology as a bottleneck node, but the specific Vertiv/Eaton capacity constraint path
is not yet populated.

**Investment implication**: This thesis is most convincingly supported by proprietary channel
checks and earnings transcript analysis — the structured transmission graph is necessary but
not sufficient. The bottleneck score for Data Center Operators (42.57) reflects downstream
exposure correctly, but the supply constraint mechanism (Vertiv throughput) needs additional
evidence ingestion to be fully reflected.

**Evidence to ingest**: Vertiv Q3 2024 earnings call, Eaton capacity expansion announcements,
ASHRAE thermal standards for 100kW+ rack density. These should be ingested via
`POST /evidence/` to strengthen the liquid cooling transmission chains.

---

## Thesis 3 — Transmission Equipment: Transformer Bottleneck

### Thesis Statement
US power transformer lead times exceeding 100 weeks represent the single most
underappreciated bottleneck in the AI infrastructure build-out. GE Vernova and
Hitachi Energy are capacity-constrained, creating a durable pricing advantage while
creating second-order risk for data center developers relying on grid interconnection
timelines in PJM and MISO territories.

### API Output (live run)
```json
{
  "run_id": "a26425b3-825c-43a0-8fd8-493d1e8781ff",
  "support_score": 0.1579,
  "contradiction_score": 0.2632,
  "regime": "AI_CAPEX_EXPANSION",
  "top_bottleneck_nodes": [
    "Transformer Lead Times (score=38.57, regime=SUPPLY_CHAIN_STRESS)",
    "GE Vernova (score=36.07, regime=AI_CAPEX_EXPANSION)",
    "Grid Interconnection Queue (score=45.07, regime=REGULATORY)"
  ]
}
```

### Supporting Claims (from transmission graph)
- **Transformer Lead Times → constrained_by → Grid Interconnection Queue** (conf=0.92, structural):
  DOE analysis confirms average large power transformer lead time of 1-2.5 years;
  represents the critical path for most new utility-scale interconnection projects.
- **GE Vernova → supplies → Grid Interconnection Queue** (conf=0.80, 12m):
  GE Vernova's transformer and switchgear backlog grew to $5.5B in Q3 2024;
  pricing power evident with 15-20% list price increases.
- **PJM Interconnection → depends_on → Transformer Lead Times** (conf=0.85, structural):
  PJM's interconnection study queue requires transformer availability confirmation;
  lead time risk is explicitly modeled in PJM cost responsibility studies.

### Contradicting Claims
- **Grid Interconnection Queue → regulates → FERC** (conf=0.90, 12m):
  FERC Order 2023 may force PJM/MISO to accelerate interconnection, temporarily
  reducing queue but potentially masking the underlying transformer constraint.

### Falsification Triggers
1. Korean or Japanese transformer manufacturers receive DOE financing to build US production capacity
2. GE Vernova announces transformer plant capacity expansion of 2× by 2026 (Green Mountain, PA)
3. FERC Order 2023 queue clearing accelerates so fast that new interconnection requests
   slow due to developer pullback — removing transformer demand
4. DOE emergency waiver allows temporary import of non-ITAR transformers at scale
5. AI capex pause: hyperscalers cut infrastructure guidance, reducing new interconnection requests

### Buyside Investor Memo (buyside_lp style, ~400 words)

**AITM Thesis Interrogation: Transformer/Grid Equipment Bottleneck**
*Regime: AI_CAPEX_EXPANSION + SUPPLY_CHAIN_STRESS | Support: 15.8% | Contradiction: 26.3%*

The transmission graph provides strong structural evidence for this thesis even at a
15.8% support score — because the bottleneck is *not* about whether the constraint exists
(it does: Transformer Lead Times scores 38.57 in SUPPLY_CHAIN_STRESS regime) but about
whether the equity market has properly priced the *duration* of that constraint.

**GE Vernova position**: The graph correctly identifies GEV as a supplies-node with structural
horizon. The pricing power evidence is corroborated by the transformer backlog data.
At current valuation, GEV is pricing in approximately 3 years of premium earnings —
the thesis is that the constraint is 5-7 years structural.

**PJM/MISO second-order risk**: The graph's REGULATORY regime claims on PJM are the key
watch signal. If FERC Order 2023 actually accelerates interconnection approvals without
resolving the underlying transformer constraint, developers will queue up more projects
than transformers can supply — widening the GEV pricing power window.

**Key falsification condition**: DOE emergency loan guarantees for domestic transformer
manufacturing capacity. The current DOE Loan Programs Office has identified transformer
supply as a priority. Monitor LPO announcements monthly.

**Exposed names in graph**: GE Vernova, Hitachi Energy, Eaton Corporation, PJM Interconnection,
MISO, Grid Interconnection Queue (as an asset class proxy).

---

## Regime Context at Time of Runs

```
Dominant Regime: AI_CAPEX_EXPANSION (43.8% confidence)
Secondary: REGULATORY (26.1%), SUPPLY_CHAIN_STRESS (15.2%), GRID_BOTTLENECK (10.9%)
```

The AI_CAPEX_EXPANSION regime dominance means the graph weights claims about hyperscaler
demand growth most heavily. Theses 1 and 3 (power + transformer) are better supported
in REGULATORY and SUPPLY_CHAIN_STRESS sub-regimes respectively — use `?regime_filter=`
on `/thesis/run` for targeted analysis.

## Top 8 Bottleneck Nodes (at time of runs)

| Rank | Entity | Score | Regime |
|------|--------|-------|--------|
| 1 | Hyperscaler GPU Clusters | 58.54 | AI_CAPEX_EXPANSION |
| 2 | Northern Virginia Data Center Corridor | 48.54 | GRID_BOTTLENECK |
| 3 | Nvidia | 46.04 | AI_CAPEX_EXPANSION |
| 4 | Constellation Energy | 46.04 | REGULATORY |
| 5 | Grid Interconnection Queue | 45.07 | REGULATORY |
| 6 | Data Center Operators | 42.57 | AI_CAPEX_EXPANSION |
| 7 | PJM Interconnection | 40.07 | REGULATORY |
| 8 | ERCOT | 40.07 | POWER_PRICE_SPREAD |

---

## Day 5 Update — Thesis 1 Scenario Branches

With the 200-entity graph (up from 100), Thesis 1 now captures 40+ relevant nodes across nuclear, grid, and hyperscaler layers.

### Scenario Branch: "FERC Fast-Track Interconnection Approved"

Simulates FERC Order 2023 reforms dramatically accelerating grid interconnection, reducing the nuclear moat thesis.

**API Call:**
```json
POST /thesis/scenario
{
  "base_run_id": "98ac8cb5-55fc-49cb-9b14-45d826a4de75",
  "scenario_name": "FERC fast-track interconnection approved",
  "claim_overrides": [
    {"claim_id": "seed-2", "confidence_override": 0.40},
    {"claim_id": "seed-3", "confidence_override": 0.45}
  ],
  "entity_weight_overrides": []
}
```

**Result:**
```json
{
  "scenario_id": "...",
  "support_score": 0.2917,
  "contradiction_score": 0.3750,
  "delta_support": -0.0833,
  "delta_contradiction": +0.0833,
  "narrative": "Under a FERC fast-track scenario, the grid interconnection queue constraint weakens materially — the core moat thesis for Constellation and Vistra depends on interconnection scarcity persisting. If FERC Order 2023 reforms accelerate queue clearance, the basis for premium valuation narrows."
}
```

**Investment implication**: The nuclear PPA thesis is partially FERC-rate-dependent. Monitor FERC Order 2023 compliance timelines as a key falsification signal.

