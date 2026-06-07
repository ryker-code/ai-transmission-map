# AI Infrastructure Transmission Map

> Maps how AI demand propagates through semiconductors, data centers, transformers, utilities, grid infrastructure, and public markets — built for equity investors running thesis interrogation.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ryker-code/ai-transmission-map)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ryker-code/ai-transmission-map)

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-Strict-3178C6?logo=typescript)
![Gemini](https://img.shields.io/badge/Gemini-1.5_Pro-4285F4?logo=google)
![BigQuery](https://img.shields.io/badge/BigQuery-dual--mode-4285F4?logo=google-cloud)
![Tests](https://img.shields.io/badge/tests-96_passing-brightgreen)

## What It Does

- **Ingests evidence** from analyst notes, URLs, charts (via Gemini vision), and voice (via Gemini audio)
- **Extracts causal claims** — structured `(subject → predicate → object)` transmission links between AI infrastructure entities
- **Scores bottlenecks** — each entity gets a 5-component weighted score showing how supply-chain-constrained it is
- **Interrogates theses** — type "power constraint benefits nuclear operators," get a support/contradiction score with traceable evidence
- **Branches scenarios** — ask "what if FERC approves fast-track interconnection?" and see the score delta vs. base case

## Live Demo

```bash
# 3-command local setup
cp .env.example .env        # add GEMINI_API_KEY (free at aistudio.google.com)
make install && make seed   # install deps, seed 200 entities + 80 claims
make dev-backend            # start FastAPI on :8000
# in a second terminal:
make dev-frontend           # start Next.js on :3000
```

Open [http://localhost:3000](http://localhost:3000).

Deploy credentials: `AITM_API_KEY=dev-key-change-in-production`
See [infrastructure/QUICK_DEPLOY.sh](infrastructure/QUICK_DEPLOY.sh) for Railway + Vercel one-command deploy.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                     │
│  Dashboard │ Graph │ Thesis │ Memo │ Evidence │ House View  │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST + SSE
┌──────────────────────▼──────────────────────────────────────┐
│                   BACKEND (FastAPI 0.115)                    │
│  /graph  /bottlenecks  /thesis  /memo  /evidence  /regime   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LANGGRAPH PIPELINE (LangGraph 0.1.x)            │
│                                                              │
│  Evidence Input                                              │
│       ↓                                                      │
│  Scout (Gemini Flash)       — entity candidate extraction   │
│       ↓                                                      │
│  Extractor (Gemini 1.5 Pro) — structured claim extraction   │
│       ↓                                                      │
│  Resolver (deterministic)   — canonical name normalization  │
│       ↓                                                      │
│  Critic (Gemini Flash)      — adversarial claim validation  │
│       ↓                                                      │
│  Scorer (5-component)       — bottleneck score computation  │
│       ↓                                                      │
│  House View Agent           — analyst conviction overlay    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│           DATABASE (BigQuery + SQLite fallback)              │
│  entities │ claims │ bottleneck_scores │ house_view          │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript strict, Tailwind CSS, shadcn/ui, react-force-graph-2d |
| Backend | FastAPI 0.115, Python 3.11, LangGraph 0.1.x, Pydantic v2 |
| LLM Models | Gemini 1.5 Pro (reasoning), Gemini Flash (extraction), Gemini Flash (audio) |
| Database | Google BigQuery (prod) + SQLite (local fallback, no GCP needed) |
| Auth | X-Api-Key header, slowapi rate limiting on write endpoints |
| Deploy | Vercel (frontend), Railway (backend) |

## Project Stats

| Metric | Value |
|--------|-------|
| Backend tests | **96 passing** |
| Frontend pages | **14+** |
| Entities in graph | **200** |
| Transmission claims | **80** |
| LLM models | **2** (Gemini 1.5 Pro + Gemini Flash — both free) |
| Evidence intake modes | **4** (URL, Image, Voice, Bloomberg parser) |
| API endpoints | **25+** |
| Build time | **7 days** (fully autonomous overnight sessions) |

## Quick Start

```bash
# Clone
git clone https://github.com/ryker-code/ai-transmission-map
cd ai-transmission-map

# Environment (GEMINI_API_KEY is free at aistudio.google.com)
cp .env.example .env

# Install + seed
make install
make seed

# Start servers
make dev-backend    # terminal 1 → http://localhost:8000
make dev-frontend   # terminal 2 → http://localhost:3000
```

## API Reference

```
GET  /health                         — liveness check
GET  /health/db                      — DB backend (BigQuery or SQLite)
GET  /graph/?regime=                 — transmission graph (nodes + edges)
GET  /bottlenecks/?limit=            — ranked bottleneck scores
POST /thesis/run                     — thesis interrogation (support/contradiction)
POST /thesis/scenario                — what-if scenario branch from base run
POST /memo/generate                  — investor memo (3 styles: LP, sellside, internal)
POST /memo/stream                    — SSE streaming memo generation
GET  /memo/{id}/pdf                  — PDF export via reportlab
POST /evidence/                      — ingest analyst note → pipeline
GET  /evidence/parse-url?url=        — URL metadata extraction
POST /evidence/image                 — multimodal chart/slide intake (Gemini vision)
POST /evidence/voice                 — voice note → Gemini audio → claims
GET  /entities/?search=              — entity search by name/ticker/alias
GET  /entities/{id}                  — entity detail (claims, score, house view)
PUT  /house-view/                    — analyst conviction override
GET  /house-view/narrative           — 3-paragraph positioning narrative (Gemini)
GET  /regime/                        — current dominant regime
GET  /regime/timeline                — 30-day regime evolution
GET  /claims/{id}/evidence           — claim audit trail
GET  /models/status                  — per-model call counts, latency, success rate
GET  /market/signals                 — 25-ticker momentum signals
GET  /watchlist/                     — starred entities with live scores
POST /watchlist/{entity_id}          — add to watchlist [auth]
POST /digest/generate                — weekly LP digest [auth]
```

## Key Features

| Feature | Detail |
|---------|--------|
| **Force-directed graph** | 200 nodes, scored sizes, color by entity type, pulsing top-5, gold ring for watched |
| **Regime filter** | ALL / AI_CAPEX / SUPPLY_CHAIN / GRID / POWER / REGULATORY — re-fetches edge set |
| **Export PNG / JSON** | Canvas export and filtered graph JSON download from graph page |
| **Scenario branches** | Parallel edge set, score delta vs. base, LLM delta narrative |
| **Streaming memo** | SSE typewriter animation, PDF download when complete |
| **5-component scorer** | evidence_intensity(0.30) + recency(0.20) + cross_source(0.20) + market(0.15) + house_view(0.15) |
| **Watchlist** | Star any entity; live score + momentum on dashboard |
| **Weekly digest** | Aggregates regime + top movers + analyst calls → LP email format |
| **Score history sparklines** | 30-day score trajectory per entity |
| **Claim feedback** | Thumbs up/down on any extracted claim |
| **BigQuery dual-mode** | Auto-detects credentials; SQLite fallback for local dev |

## Interview Resources

- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — minute-by-minute 18-minute live demo walkthrough
- [docs/ELEVATOR_PITCH.md](docs/ELEVATOR_PITCH.md) — 30-second, 2-minute, and 5-minute versions
- [docs/ARCHITECTURE_DEEP_DIVE.md](docs/ARCHITECTURE_DEEP_DIVE.md) — scorer design, BigQuery schema, multi-model routing
- [docs/INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md) — common questions with answers
- [docs/demo_theses.md](docs/demo_theses.md) — 3 interview-ready thesis runs

## Test Suite

```bash
cd backend && pytest tests/ -v    # 96 tests
cd frontend && npm run build      # TypeScript strict check
```
