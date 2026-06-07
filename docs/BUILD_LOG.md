# BUILD_LOG — Day 3

**Completed:** Sun Jun 8 05:05 UTC 2026
**Duration:** ~3.5 hours (Day 3 autonomous session)
**Status:** All Day 3 phases complete — no blockers

## Day 3 Files Created / Modified

### New Backend Files
- `backend/agents/scorer.py` — full 5-component weighted scorer (evidence×0.30 + recency×0.20 + cross_source×0.25 + market×0.15 + house_view×0.10), normalized 0-100
- `backend/agents/resolver.py` — EntityResolver class with alias index, ticker resolution, merge_duplicate
- `backend/agents/house_view.py` — apply_house_view() with conviction bonuses (±10pt), pinned entity tracking
- `backend/db/claims_store.py` — in-memory accepted claims pool (pipeline → scorer continuity)
- `backend/db/house_view_store.py` — in-memory conviction/weight store for bottleneck scoring
- `backend/db/run_cache.py` — shared thesis run store (thesis→memo wiring)
- `backend/tools/bloomberg_parser.py` — URL metadata parser (ToS-compliant, no article content)
- `backend/tools/image_intake.py` — Claude Opus vision claim extraction from PNG/JPEG charts

### Updated Backend Files
- `backend/api/routes/bottlenecks.py` — calls scorer + apply_house_view
- `backend/api/routes/evidence.py` — bloomberg enrichment + /evidence/image + /evidence/parse-url
- `backend/api/routes/house_view.py` — SQLite persistence + list endpoint
- `backend/api/routes/entities.py` — real implementation (seed + filters)
- `backend/agents/extractor.py` — run_resolver() delegates to EntityResolver
- `backend/agents/critic.py` — claims_store + regime update wiring
- `backend/requirements.txt` — added python-multipart==0.0.9

### New Tests
- `backend/tests/test_scorer.py` — 4 tests (ranking, range, components, filter)
- `backend/tests/test_resolver.py` — 8 tests (exact, ticker, alias, unknown, batch, merge, singleton)
- `backend/tests/test_house_view.py` — 5 tests (weight, high bonus, low penalty, pinned, passthrough)
- `backend/tests/test_bloomberg_parser.py` — 9 tests (5 parametrized URLs + 4 focused)
- `backend/tests/test_image_intake.py` — 4 async tests (claims, structure, empty, range)
- `backend/tests/test_health.py` — expanded +5 tests (falsifiers, memo, regime, parse-url)

### Frontend Updates
- `frontend/app/evidence/page.tsx` — Parse URL button, image upload section
- `frontend/app/page.tsx` — live stat cards via SWR (entity count, claims, regime)
- `frontend/next.config.ts` — standalone output, bloomberg image domain

### Docs
- `docs/demo_theses.md` — 3 interview-ready theses with live API output
- `docs/OVERNIGHT_PROMPT_DAY3.md` — pulled from origin/main (user-authored)
- `README.md` — polished with ASCII architecture diagram, badges, feature/agent tables

## Test Results (Day 3 Final)

```
42 passed, 3 warnings in 4.51s

test_bloomberg_parser.py  9 tests  ✓
test_health.py           12 tests  ✓
test_house_view.py        5 tests  ✓
test_image_intake.py      4 tests  ✓
test_resolver.py          8 tests  ✓
test_scorer.py            4 tests  ✓
```

## Frontend Build (Day 3 Final)

```
✓ Next.js build successful (standalone output)
✓ TypeScript check passed
✓ 7 routes: /, /evidence, /graph, /house-view, /memo, /thesis, /_not-found
```

## Known Issues (Day 3)
- All Day 1 + Day 2 deprecation items resolved
- No first-party warnings in test suite
- Third-party warnings (google.protobuf, pydantic v1 config) are non-blocking

## Deployment Status
- Vercel: configured (vercel.json + standalone next.config.ts); deploy with button in README
- Cloud Run: Dockerfile + cloudbuild.yaml ready; pending GCP project setup

## Day 4 Objectives
1. Voice note intake (POST /evidence/voice — Whisper or Google Speech-to-Text)
2. Regime timeline view (app/regime/page.tsx — how regime shifted over ingested evidence)
3. Entity detail pages (app/entities/[id]/page.tsx — claims, score history, house view)
4. PDF memo export (GET /export/thesis/{run_id}.pdf — reportlab or weasyprint)
5. Live Vercel deployment with real API keys

---

# BUILD_LOG — Day 1

**Completed:** Sun Jun 7 03:31 UTC 2026  
**Duration:** ~17 minutes  
**Status:** All phases complete — no blockers

---

## Files Created

### Root
- `CLAUDE.md` — project identity and autonomous run rules
- `ANTIGRAVITY.md` — model selection and permission policy
- `.gitignore`
- `.env.example`
- `Makefile`
- `README.md`

### Backend
- `backend/__init__.py`
- `backend/config.py` — pydantic-settings config
- `backend/main.py` — FastAPI app with 7 routers
- `backend/requirements.txt`
- `backend/api/__init__.py`
- `backend/api/schemas.py` — 10 Pydantic models
- `backend/api/routes/__init__.py`
- `backend/api/routes/evidence.py`
- `backend/api/routes/entities.py`
- `backend/api/routes/graph.py`
- `backend/api/routes/bottlenecks.py`
- `backend/api/routes/thesis.py`
- `backend/api/routes/memo.py`
- `backend/api/routes/house_view.py`
- `backend/agents/__init__.py`
- `backend/db/__init__.py`
- `backend/db/bigquery_client.py` — BigQuery + SQLite fallback
- `backend/db/seed_loader.py`
- `backend/db/seed_data/entities.json` — 100 entities
- `backend/db/seed_data/transmission_chains.json` — 30 chains
- `backend/db/migrations/` (directory)
- `backend/tools/__init__.py`
- `backend/prompts/` (directory)
- `backend/tests/__init__.py`
- `backend/tests/test_health.py` — 4 tests

### Frontend
- `frontend/` — Next.js 16.2.7 (TypeScript, Tailwind, ESLint, App Router)
- `frontend/lib/types.ts` — TypeScript interfaces for all schemas
- `frontend/lib/api-client.ts` — typed API client
- `frontend/app/layout.tsx` — dark sidebar layout
- `frontend/app/page.tsx` — bottleneck dashboard skeleton
- `frontend/app/graph/page.tsx` — graph explorer placeholder
- `frontend/app/thesis/page.tsx` — thesis workspace
- `frontend/app/memo/page.tsx` — memo generator

### Infrastructure
- `infrastructure/bigquery/schema_init.sql` — 9 table DDLs
- `infrastructure/cloud_run/` (directory)

### Docs
- `docs/architecture.md`
- `docs/BUILD_LOG.md` (this file)

---

## Test Results

```
4 passed, 5 warnings in 1.06s
- test_health ✓
- test_graph_route ✓
- test_bottlenecks_route ✓
- test_evidence_ingest ✓
```

## Frontend Build

```
✓ Next.js 16.2.7 build successful
✓ TypeScript check passed
✓ 5 routes compiled: /, /graph, /thesis, /memo, /_not-found
```

## Seed Loader

```
✓ 100 entities loaded (SQLite stub — no GCP creds)
✓ 30 transmission claims loaded
```

## Issues Encountered

1. **langchain version conflict** — pinned versions in requirements.txt had incompatible sub-dependencies. Fixed by using range constraints (`>=x,<y`) for langchain-core, langchain-anthropic, langchain-google-genai, langgraph.

2. **Frontend bootstrap conflict** — `create-next-app` could not scaffold into a pre-created directory with subdirectories. Fixed by removing frontend dir and recreating.

3. **Seed loader module path** — running as `python backend/db/seed_loader.py` failed; must be invoked as `python -m backend.db.seed_loader`.

---

## Day 2 Objectives

1. Build `backend/agents/orchestrator.py` — LangGraph state machine wiring Scout → Extractor → Resolver → Critic → Scorer
2. Build `backend/agents/extractor.py` — Claude claude-opus-4-5 claim extraction with structured output
3. Build `backend/agents/critic.py` — Gemini Flash confidence scoring and contradiction detection
4. Wire `POST /evidence` to trigger full orchestrator pipeline
5. Implement `GET /graph/` with real BigQuery query returning seeded nodes and edges
6. Implement `GET /bottlenecks/` with real scoring query
7. Implement `POST /thesis/run` with real graph BFS + claim matching
8. Build react-force-graph-2d graph explorer component
9. Build BottleneckBoard component on dashboard
10. Add real-time regime detection based on claim regime_tag distribution
