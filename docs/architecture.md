# Architecture — AI Transmission Map

## System Overview

The AI Transmission Map is a production-grade investor thesis tool that models how AI demand propagates through the US infrastructure stack — from silicon supply chains through data center construction, power grid interconnection, transformer manufacturing, utility capacity, and into public equity markets. The system maintains a structured knowledge graph of entities (companies, assets, regulators, RTOs) connected by directional transmission claims (e.g. "Nvidia supplies Hyperscaler GPU Clusters", "Grid Interconnection Queue constrained_by Transformer Lead Times") with confidence scores, regime tags, and time horizons.

The backend is a FastAPI service (Python 3.11, Pydantic v2) that orchestrates a LangGraph multi-agent pipeline for evidence ingestion and claim extraction. Evidence notes (Bloomberg, SEC filings, utility interconnection filings) are processed by a Scout → Extractor → Resolver → Critic → Scorer pipeline, with each agent using either Claude claude-opus-4-5 (complex reasoning, multi-hop claim synthesis) or Gemini 2.0 Flash (fast entity extraction and structured output). All structured data persists in Google BigQuery, with a SQLite fallback for local development.

The frontend is a Next.js 15 application with a dark-themed investor dashboard. The primary views are: a Bottleneck Dashboard (ranked transmission chokepoints by composite score), a force-directed Graph Explorer (react-force-graph-2d), a Thesis Workspace (freeform thesis interrogation against the graph), and a Memo Generator (AI-drafted buyside/sellside memos from thesis runs). The entire stack is designed for equity investors running active thesis interrogation — not for data engineering or operational monitoring.

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Evidence Sources                          │
│  Bloomberg Terminal  │  SEC EDGAR  │  Utility Filings       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ingestion Layer                             │
│  POST /evidence  →  EvidenceIngest schema validation        │
│  Source document stored  →  analyst_note indexed            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               LangGraph Agent Pipeline                       │
│                                                              │
│  Scout Agent          →  identifies relevant entities       │
│  Extractor Agent      →  extracts structured claims         │
│  Resolver Agent       →  deduplicates & canonicalizes       │
│  Critic Agent         →  flags low-confidence claims        │
│  Scorer Agent         →  computes bottleneck scores         │
│  Memo Agent           →  drafts investor memos              │
│                                                              │
│  Models: Claude claude-opus-4-5 (reasoning) + Gemini Flash (extraction)│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Google BigQuery                             │
│  aitm.entities  │  aitm.claims  │  aitm.bottleneck_scores  │
│  aitm.thesis_runs  │  aitm.memo_outputs  │  aitm.house_view │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  /graph  /bottlenecks  /thesis/run  /memo/generate          │
│  /evidence  /entities  /house-view                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Next.js Frontend                             │
│  Dashboard  │  Graph Explorer  │  Thesis  │  Memo           │
│  Dark theme, Tailwind CSS, shadcn/ui, react-force-graph-2d  │
└─────────────────────────────────────────────────────────────┘
```

## Agent Pipeline — Evidence Ingest

```
POST /evidence
      │
      ▼
  Scout Agent (Gemini Flash)
  - Identifies entities mentioned in analyst_note
  - Emits: entity_candidates[]
      │
      ▼
  Extractor Agent (Claude claude-opus-4-5)
  - Extracts structured transmission claims
  - Maps to predicates: supplies, depends_on, constrained_by, etc.
  - Emits: raw_claims[]
      │
      ▼
  Resolver Agent (Gemini Flash)
  - Deduplicates against existing graph
  - Canonicalizes entity names to registry
  - Emits: resolved_claims[]
      │
      ▼
  Critic Agent (Claude claude-opus-4-5)
  - Evaluates claim confidence against evidence base
  - Flags contradictions with existing accepted claims
  - Emits: critiqued_claims[] with confidence adjustments
      │
      ▼
  Scorer Agent (Gemini Flash)
  - Recomputes bottleneck scores for affected entities
  - Factors: evidence_intensity, recency, cross_source_agreement,
             market_confirmation, house_view_weight
  - Writes to aitm.bottleneck_scores
      │
      ▼
  Returns EvidenceResponse: entity count, claim count, status
```

## Data Flow — Thesis Run

```
POST /thesis/run {thesis: str, depth: int}
      │
      ▼
  Graph Slice Query
  - BFS from all mentioned entities to depth N
  - Filters by regime_filter if provided
      │
      ▼
  Claim Matching (Claude claude-opus-4-5)
  - Finds supporting claims (confidence-weighted)
  - Finds contradicting claims
  - Identifies exposed entities in the subgraph
      │
      ▼
  Falsification Trigger Generation
  - What events would break this thesis?
  - Grounded in actual claims in the graph
      │
      ▼
  Returns ThesisRunResponse
  - support_score, contradiction_score
  - supporting_claims[], contradicting_claims[]
  - exposed_entities[], falsification_triggers[]
  - graph_slice (subgraph for visualization)
```
