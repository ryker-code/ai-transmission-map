# AI Infrastructure Transmission Map

> Maps how AI demand propagates through semiconductors, data centers, transformers, utilities, grid infrastructure, and public markets — built for equity investors running thesis interrogation.

![screenshot](docs/screenshot.png)

## Quick Start

```bash
# 1. Clone
git clone <repo-url>
cd ai-transmission-map

# 2. Environment
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT

# 3. Install dependencies
make install

# 4. Seed the graph
make seed

# 5. Run backend (port 8000)
make dev-backend

# 6. Run frontend (port 3000)
make dev-frontend
```

Open [http://localhost:3000](http://localhost:3000) to see the dashboard.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design, agent pipeline, and data flow diagrams.

## Tech Stack

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1.x-blue)
![BigQuery](https://img.shields.io/badge/BigQuery-Google_Cloud-4285F4?logo=google-cloud)
![Claude AI](https://img.shields.io/badge/Claude-claude--opus--4--5-orange)
![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-blue?logo=google)

## Key Features

- **Transmission Graph** — 100+ entities, 30+ directional claims with confidence scores and regime tags
- **Bottleneck Scoring** — composite score across evidence intensity, recency, cross-source agreement, market confirmation, and house view weight
- **Thesis Interrogation** — freeform thesis run against the graph; returns support/contradiction scores, exposed entities, and falsification triggers
- **Memo Generation** — AI-drafted buyside LP notes, sellside notes, or internal briefs from thesis runs
- **House View** — analyst conviction weights and annotations per entity
- **SQLite Fallback** — full local dev without GCP credentials
