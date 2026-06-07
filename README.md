# AI Infrastructure Transmission Map

> Maps how AI demand propagates through semiconductors, data centers, transformers, utilities, grid infrastructure, and public markets — built for equity investors running thesis interrogation.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ryker-code/ai-transmission-map)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ryker-code/ai-transmission-map)

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1.x-blue)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-Strict-3178C6?logo=typescript)
![BigQuery](https://img.shields.io/badge/BigQuery-Google_Cloud-4285F4?logo=google-cloud)
![Claude AI](https://img.shields.io/badge/Claude-Opus--4--5-orange)
![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-blue?logo=google)
![Tests](https://img.shields.io/badge/tests-69_passing-brightgreen)

## Live Demo

| Surface | URL |
|---------|-----|
| Frontend (Vercel) | Run `railway up` from local machine — see [QUICK_DEPLOY.md](infrastructure/QUICK_DEPLOY.md) |
| Backend API (Railway) | `railway up` — deploys in ~3 minutes, auto-seeds 200 entities + 80 claims |
| API docs (local) | http://localhost:8000/docs |
| Health check (local) | http://localhost:8000/health |

> **3-command deploy**: `npm i -g @railway/cli && railway login && railway up`
> See [infrastructure/QUICK_DEPLOY.md](infrastructure/QUICK_DEPLOY.md) for full Vercel + Railway guide.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/ryker-code/ai-transmission-map
cd ai-transmission-map

# 2. Environment
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT

# 3. Install dependencies
make install

# 4. Seed the graph (SQLite fallback — no GCP required)
make seed

# 5. Run backend (port 8000)
make dev-backend

# 6. Run frontend (port 3000)
make dev-frontend
```

Open [http://localhost:3000](http://localhost:3000).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                     │
│  Dashboard │ Graph │ Thesis │ Memo │ Evidence │ House View  │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST + WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                   BACKEND (FastAPI 0.115)                    │
│  /graph  /bottlenecks  /thesis  /memo  /evidence  /regime   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LANGGRAPH PIPELINE (LangGraph 0.1.x)            │
│                                                              │
│  Evidence Note                                               │
│      │                                                       │
│      ▼                                                       │
│  Scout (Gemini 2.0 Flash)   — entity candidate extraction   │
│      │                                                       │
│      ▼                                                       │
│  Extractor (Claude Opus)    — structured claim extraction    │
│      │                                                       │
│      ▼                                                       │
│  Resolver (EntityResolver)  — canonical name normalization  │
│      │                                                       │
│      ▼                                                       │
│  Critic (Claude Opus)       — adversarial claim validation  │
│      │                                                       │
│      ▼                                                       │
│  Scorer (5-component)       — bottleneck score computation  │
│      │                                                       │
│      ▼                                                       │
│  House View Agent           — analyst conviction overlay    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│           DATABASE (BigQuery + SQLite fallback)              │
│  entities │ claims │ bottleneck_scores │ house_view          │
│  Seed: 100 entities, 30 transmission chains                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Transmission Graph** | 100 entities, 30 directional claims with confidence scores and regime tags |
| **Full Weighted Scorer** | 5-component score: evidence intensity×0.30 + recency×0.20 + cross-source×0.25 + market×0.15 + house view×0.10 |
| **Entity Resolver** | Alias index for 100+ entities — resolves tickers, common names, partial names |
| **Thesis Interrogation** | BFS subgraph extraction + Claude Opus scoring → support/contradiction + falsification triggers |
| **Memo Generation** | Buyside LP notes, sellside notes, and internal briefs from thesis runs |
| **House View Agent** | Conviction overrides (high/medium/low) with ±10pt score adjustment + SQLite persistence |
| **Bloomberg Parser** | URL metadata extraction (title, tags, date, entities) without fetching article content |
| **Image Intake** | Claude Opus vision extracts claims from charts and slides (PNG/JPEG) |
| **Regime Detection** | Confidence-weighted dominant regime from active claim graph; updates on ingest |
| **SQLite Fallback** | Full local dev without GCP credentials |

## Agent Models

| Agent | Model | Role |
|-------|-------|------|
| Scout | Gemini 2.0 Flash | Fast entity candidate extraction |
| Extractor | Claude claude-opus-4-5 | Multi-hop transmission claim extraction |
| Resolver | EntityResolver (deterministic) | Alias normalization, no LLM cost |
| Critic | Claude claude-opus-4-5 | Adversarial claim validation |
| Scorer | Deterministic (5-component) | Bottleneck score computation |
| House View | Deterministic (conviction rules) | Analyst overlay application |
| Thesis | Claude claude-opus-4-5 | BFS subgraph + support/contradiction scoring |
| Memo | Claude claude-opus-4-5 | Investor memo generation (3 styles) |
| Image Intake | Claude claude-opus-4-5 | Multimodal chart/slide claim extraction |

## Demo Theses

See [docs/demo_theses.md](docs/demo_theses.md) for three interview-ready thesis interrogations:

1. **Power Constraint / Nuclear Moat** — Constellation Energy, Vistra Corp, Talen Energy
2. **Thermal Management / Liquid Cooling** — Vertiv Holdings, Eaton Corporation
3. **Transmission Equipment / Transformer Bottleneck** — GE Vernova, Hitachi Energy

## Interview Showcase

See [`docs/INTERVIEW_GUIDE.md`](docs/INTERVIEW_GUIDE.md) for:
- 30-second pitch
- Five technical deep-dives
- Worked example of bottleneck score calculation
- Common interview questions with answers
- 3-minute live demo flow

## Technical Highlights

| Highlight | Detail |
|-----------|--------|
| **5-component scorer** | `evidence_intensity(0.30) + recency_decay(0.20) + cross_source(0.25) + market_confirmation(0.15) + house_view(0.10)` normalized 0–100 |
| **LangGraph determinism** | Typed `GraphState`, 5-node pipeline prevents prompt soup; each node has single responsibility |
| **Alias resolver singleton** | Built once, cached; handles tickers + partial names + multi-word sliding window |
| **Three intake modalities** | Bloomberg URL (no HTTP), Claude Opus vision, Whisper + Claude claim extraction |
| **Real-time regime shift** | New evidence updates `_dynamic_claims` pool; regime recomputed on every `/regime/` request |
| **PDF export** | reportlab renders investor memo with bottleneck table and key entity section |
| **59 tests** | scorer, resolver, house_view, bloomberg_parser, image_intake, voice_intake, phase4 routes |
| **SQLite offline mode** | Full dev loop without GCP credentials — `USE_BIGQUERY=false` flag |

## API Reference

```
GET  /health                         — liveness check
GET  /graph/?regime=                 — transmission graph (nodes + edges)
GET  /bottlenecks/?limit=            — ranked bottleneck scores
POST /thesis/run                     — thesis interrogation
POST /memo/generate                  — investor memo from thesis run
GET  /memo/{memo_id}/pdf             — PDF export (reportlab)
POST /evidence/                      — ingest note → async pipeline
GET  /evidence/parse-url?url=        — URL metadata extraction
POST /evidence/image                 — multimodal chart/slide intake
POST /evidence/voice                 — voice note → Whisper → claims
GET  /entities/?search=              — entity search by name/ticker/alias
GET  /entities/{id}                  — entity detail (claims, score, house view)
PUT  /house-view/                    — analyst conviction override
GET  /house-view/narrative           — Claude Opus 3-paragraph positioning narrative
GET  /regime/                        — current dominant regime
GET  /regime/timeline                — 30-day regime evolution
GET  /claims/{id}/evidence           — claim audit trail
```

## Deployment

**Frontend → Vercel**: click the Deploy button above, or:
```bash
cd frontend && npx vercel --prod
```

**Backend → Cloud Run**: see [infrastructure/cloud_run/](infrastructure/cloud_run/) for Dockerfile and Cloud Build config.

## Test Suite

```bash
make test          # 59 tests across scorer, resolver, house view, bloomberg parser, image intake, voice, phase4 routes
```

## Project Structure

```
ai-transmission-map/
├── backend/
│   ├── agents/          # LangGraph pipeline (scout, extractor, resolver, critic, scorer, house_view, memo)
│   ├── agents/          # LangGraph pipeline + scorer, resolver, house_view, memo
│   ├── api/routes/      # FastAPI routes (10 routers incl. claims, regime/timeline)
│   ├── db/              # BigQuery client, SQLite fallback, seed data (100 entities, 30 chains)
│   ├── scripts/         # demo_run.py quick-demo
│   ├── tools/           # Regime detector, Bloomberg parser, image/voice intake, PDF export
│   └── tests/           # 59 tests
├── frontend/
│   ├── app/             # 9 Next.js App Router pages (+ entities/[id], regime)
│   ├── components/      # TransmissionGraph.tsx, BottleneckBoard.tsx, EntitySearch.tsx
│   └── lib/             # API client, TypeScript types
├── infrastructure/
│   └── cloud_run/       # Dockerfile, cloudbuild.yaml
└── docs/
    ├── architecture.md
    ├── demo_theses.md
    └── known_issues.md
```
