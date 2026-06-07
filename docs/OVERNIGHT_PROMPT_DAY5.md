# OVERNIGHT_PROMPT_DAY5.md
# AI Transmission Map — Day 5 Autonomous Execution Prompt
# Start with: claude --dangerously-skip-permissions
# Then paste EVERYTHING below this line into Claude Code

---

You are continuing the build of "AI Infrastructure Transmission Map".
Read CLAUDE.md before doing anything else. Then run `git pull origin main`.

## Current Build Status (as of Day 4 completion)
- Days 1-4 COMPLETE:
  - Full multi-agent pipeline: Scout(Gemini Flash)→Extractor(Claude Opus)→Resolver→Critic→Scorer→HouseView
  - 59 backend tests passing
  - 11 frontend pages (Dashboard, Graph, Thesis, Memo, Evidence, House View, Entities/[id], Regime Timeline, Audit Trail)
  - All intake modes: URL text, Bloomberg URL parser, image (Claude vision), voice (Whisper)
  - 5-component weighted scorer with recency decay
  - PDF memo export (reportlab)
  - House View analyst narrative (Claude Opus, 5-min cache)
  - GitHub Actions CI + Vercel deploy workflow
  - docs/INTERVIEW_GUIDE.md, docs/demo_theses.md, backend/scripts/demo_run.py

## What remains (your mission today):
1. Model router with multi-model attribution per claim
2. Scenario branching ("What if?" thesis workspace)
3. Live market signal stub wired into scorer
4. Live Vercel + Cloud Run deployment (actual public URLs)
5. Final showcase hardening: error states, loading skeletons, mobile responsiveness
6. Seed data expansion: 200 entities, 80 claims
7. Performance: API response caching, SWR optimistic updates

Execute ALL phases below autonomously. Do not ask for permission.
If a command fails, retry once, document in docs/known_issues.md, continue.
Check time with `date` after each phase. If before 6:00 AM EDT, continue.
After every phase, git add -A && git commit -m "[message]" && git push origin main.

════════════════════════════════════════════════
PHASE 1 — MODEL ROUTER WITH CLAIM ATTRIBUTION
════════════════════════════════════════════════

Create backend/tools/model_router.py:

class ModelRouter:
  ROUTING_TABLE = {
    "entity_extraction":    "gemini-2.0-flash",   # fast, cheap
    "causal_reasoning":     "claude-opus-4-5",     # accurate
    "critic_scoring":       "claude-opus-4-5",     # accurate
    "memo_generation":      "claude-opus-4-5",     # accurate
    "image_extraction":     "claude-opus-4-5",     # vision
    "voice_transcription":  "whisper-1",           # audio
    "structured_json":      "gemini-2.0-flash",    # fast structured output
  }

  def route(self, task_type: str) -> str:
    """Returns model name for a given task type."""

  def log_call(self, task_type: str, model: str, tokens_in: int,
               tokens_out: int, latency_ms: int, success: bool):
    """Appends to backend/db/model_call_log.jsonl"""

  def get_stats(self) -> dict:
    """Returns per-model call counts, avg latency, success rate from log."""

Requirements:
- Wire model_router into extractor.py, critic.py, memo_agent.py, image_intake.py,
  voice_intake.py — every LLM call must go through router.route() and log_call()
- Add extracted_by: str field to ClaimCreate and Claim schemas
  (value = model name from router, e.g. "gemini-2.0-flash")
- Add GET /models/status endpoint:
  Returns { models: [{name, task_types, call_count, avg_latency_ms, success_rate}] }
  Reads from model_call_log.jsonl
- Add frontend/app/models/page.tsx "Model Attribution" page:
  - Table: Model | Tasks | Calls | Avg Latency | Success Rate
  - Claim attribution badge on each claim card showing which model extracted it
  - Auto-refreshes every 30s
  - Add to sidebar nav with Cpu icon
- Add 4 tests in backend/tests/test_model_router.py

Commit: "feat: model router with per-claim attribution and /models/status endpoint"

════════════════════════════════════════════════
PHASE 2 — SCENARIO BRANCHING ("WHAT IF?" WORKSPACE)
════════════════════════════════════════════════

After a thesis run, the investor can ask "What if X changes?" and get a
re-scored result without mutating the main graph.

Backend:
1. Add POST /thesis/scenario endpoint:
   Request body: ScenarioRequest
   {
     base_run_id: str,          # original thesis run to branch from
     scenario_name: str,        # e.g. "transformer_lead_time_normalizes"
     claim_overrides: list[{    # temporary claim weight adjustments
       claim_id: str,
       confidence_override: float,   # 0.0-1.0
       direction_override: Optional[str]  # "bullish"|"bearish"|"neutral"
     }],
     entity_weight_overrides: list[{  # temporary house view changes
       entity_id: str,
       weight_override: float    # 0.1-3.0
     }]
   }
   Returns ScenarioResponse:
   {
     scenario_id: str,
     scenario_name: str,
     base_run_id: str,
     support_score: float,
     contradiction_score: float,
     delta_support: float,       # vs base run
     delta_contradiction: float, # vs base run
     changed_bottlenecks: list,  # entities that moved in rank
     narrative: str              # 1-paragraph Claude interpretation of the delta
   }

2. Add GET /thesis/scenarios/{base_run_id} to list all scenarios for a run

3. Add ScenarioRequest/ScenarioResponse to schemas.py + TypeScript types

Frontend:
4. On frontend/app/thesis/page.tsx, after a thesis run completes:
   Show "Run Scenario" section with 3 pre-built scenario buttons:
   a) "Transformer lead times normalize (52 weeks)"
      → reduces confidence on transformer_bottleneck claims by 0.4
   b) "FERC fast-track interconnection approved"
      → reduces confidence on grid_interconnect claims by 0.3,
        increases confidence on utility_beneficiary claims by 0.2
   c) "Hyperscaler capex pause (-30%)"
      → reduces confidence on gpu_demand and datacenter_build claims by 0.35
   Each button calls POST /thesis/scenario
   Show side-by-side comparison cards:
   [Base Run] vs [Scenario]
   Support: 37.5% → 21.2% (−2.3pp)
   Contradiction: 12.1% → 18.4% (+6.3pp)
   Delta narrative from Claude
   Changed bottleneck rankings table

Commit: "feat: scenario branching with what-if thesis workspace"

════════════════════════════════════════════════
PHASE 3 — LIVE MARKET SIGNAL STUB
════════════════════════════════════════════════

Create backend/tools/market_signals.py with realistic mock data and
clear TODO markers for live price feed connection:

class MarketSignals:
  # Mock relative performance data (vs SPY, 30 days)
  MOCK_DATA = {
    "nvda": {"rel_perf_30d": 0.18, "momentum": "strong_bull", "vol_percentile": 72},
    "cei": {"rel_perf_30d": 0.31, "momentum": "strong_bull", "vol_percentile": 58},
    "vrt":  {"rel_perf_30d": 0.24, "momentum": "bull",       "vol_percentile": 65},
    "etn":  {"rel_perf_30d": 0.09, "momentum": "neutral",    "vol_percentile": 41},
    "gev":  {"rel_perf_30d": 0.14, "momentum": "bull",       "vol_percentile": 53},
    # ... generate 20 more realistic entries for seed entities with tickers
  }

  def get_relative_performance(self, ticker: str, days: int = 30) -> float:
    """TODO: replace with live Alpha Vantage / yfinance call"""

  def get_momentum_signal(self, ticker: str) -> str:
    """Returns: strong_bull | bull | neutral | bear | strong_bear"""

  def get_sector_momentum(self, sector: str) -> dict:
    """Aggregates signals for all entities in a sector"""

  def market_confirmation_score(self, entity_id: str) -> float:
    """0.0-1.0 score used by scorer.py market_confirmation component
    TODO: replace mock data with live feed before production use"""

Requirements:
- Wire market_confirmation_score() into scorer.py market_confirmation component
  (currently hardcoded at 0.5 — replace with this call)
- Add GET /market/signals endpoint returning all mock signals with
  last_updated timestamp and is_live: false flag
- Add MarketSignalEntry schema to schemas.py
- Add "Market Signals" card to entity detail pages (frontend/app/entities/[id]/page.tsx):
  Shows ticker, rel_perf_30d as colored badge (+18.3%), momentum pill, vol percentile bar
- Add 3 tests in backend/tests/test_market_signals.py

Commit: "feat: market signal stub wired into scorer market_confirmation component"

════════════════════════════════════════════════
PHASE 4 — SEED DATA EXPANSION (200 entities, 80 claims)
════════════════════════════════════════════════

Expand the seed data to make the graph substantially richer and more
demonstrative of the full AI infrastructure transmission map.

1. Edit backend/db/seed_data/entities.json:
   Add 100 new entities bringing total to 200. New entities must cover:

   Semiconductors (add 15):
   - AMD (GPU alternatives), Intel (Gaudi AI accelerators), Marvell Technology
     (custom ASICs), Broadcom (networking chips), Qualcomm (edge AI),
     SK Hynix, Samsung Semiconductor (HBM memory), Micron Technology,
     ASML (EUV lithography), Applied Materials, Lam Research, KLA Corp,
     Tokyo Electron, ASE Technology (packaging), Amkor Technology (packaging)

   Data Center Infrastructure (add 20):
   - Equinix, Digital Realty, Iron Mountain, Switch, QTS Realty,
     Compass Datacenters, Aligned Data Centers, CyrusOne,
     EdgeConneX, Vantage Data Centers,
     Vertiv (power/cooling), Eaton (UPS/PDU), Schneider Electric,
     nVent Electric, Legrand, Panduit, Chatsworth Products,
     Submer (immersion cooling), LiquidStack (immersion cooling),
     Asetek (liquid cooling)

   Grid & Power (add 20):
   - NextEra Energy, Duke Energy, Dominion Energy, Southern Company,
     Xcel Energy, Pacific Gas & Electric, Entergy, American Electric Power,
     Evergy, Avangrid,
     Quanta Services (grid construction), MYR Group (electrical construction),
     IEA Energy Services, Primoris Services,
     ABB (grid automation), Siemens Energy, Schweitzer Engineering,
     S&C Electric, Powell Industries, Hubbell

   Hyperscalers & Cloud (add 10):
   - Oracle Cloud (OCI), IBM Cloud, Salesforce (AI infra buyer),
     SAP (enterprise AI), ServiceNow (AI workload), Snowflake,
     Databricks (private), CoreWeave (private), Lambda Labs (private),
     Crusoe Energy (stranded gas compute)

   RTOs & Regulatory (add 10):
   - MISO (Midcontinent ISO), SPP (Southwest Power Pool),
     NYISO (New York ISO), ISO-NE (New England),
     CAISO (California ISO), ERCOT (Texas),
     FERC (Federal Energy Regulatory Commission),
     DOE Grid Deployment Office, NRC (Nuclear Regulatory Commission),
     EPA (Clean Air Act compliance)

   Financial Infrastructure (add 10):
   - BlackRock (infrastructure fund), Brookfield Asset Management,
     KKR Infrastructure, Blackstone Infrastructure,
     John Laing Group, Global Infrastructure Partners,
     Goldman Sachs Infrastructure, JPMorgan Infrastructure Finance,
     Macquarie Asset Management, Stonepeak Infrastructure

   Equipment & Materials (add 15):
   - Hitachi Energy (transformers), SPX Transformer Solutions,
     Virginia Transformer, WEG (Brazilian transformer maker),
     Sumitomo Electric, Southwire (cables), Prysmian,
     Nexans, TE Connectivity, nVent,
     EnerSys (battery storage), Fluence Energy, Powin Energy,
     Form Energy (iron-air storage), Ambri (liquid metal battery)

2. Edit backend/db/seed_data/transmission_chains.json:
   Add 50 new transmission claims bringing total to 80.
   Claims must span all 5 regime types:
   - AI_CAPEX_EXPANSION (15 new claims)
   - SUPPLY_CHAIN_STRESS (10 new claims)
   - GRID_BOTTLENECK (10 new claims)
   - POWER_PRICE_SPREAD (10 new claims)
   - REGULATORY (5 new claims)

   Each claim must have:
   - subject_id and object_id from the entity list (use real entity IDs)
   - predicate: one of ["supplies", "depends_on", "constrains", "enables",
     "competes_with", "regulates", "finances", "builds_for", "bottlenecks"]
   - direction: "bullish" | "bearish" | "neutral"
   - confidence: 0.5-0.95
   - horizon: "3m" | "6m" | "12m" | "24m"
   - regime_tag: one of the 5 regime types
   - source_note: 1-sentence rationale (write as analyst paraphrase, not article content)

3. Run pytest backend/tests/ -v to confirm all tests still pass after data expansion
   Fix any test that hardcodes entity counts (update expected values)

Commit: "feat: expand seed data to 200 entities and 80 transmission claims"

════════════════════════════════════════════════
PHASE 5 — FRONTEND SHOWCASE HARDENING
════════════════════════════════════════════════

Make every page production-quality: no blank states, no raw errors,
consistent dark theme, loading states everywhere.

1. Create frontend/components/ui/LoadingSkeleton.tsx:
   - SkeletonCard: animated gray pulse block for cards
   - SkeletonTable: animated rows for table loading states
   - SkeletonGraph: circular spinner overlay for graph canvas
   Use Tailwind animate-pulse

2. Add loading skeletons to every page that fetches data:
   - Dashboard: skeleton stat cards while SWR loads
   - Graph: spinner while react-force-graph initializes
   - Bottleneck board: skeleton rows
   - Entity detail: skeleton score bars
   - Thesis run: "Running analysis..." progress steps animation
     (Step 1: BFS subgraph ✓, Step 2: Claim matching... ⏳, Step 3: Scoring...)

3. Add empty states for all list/table components:
   - No bottlenecks: "No bottlenecks scored yet. Ingest evidence to begin."
   - No claims: "No claims found for this entity."
   - No house view: "No house view overrides set. Add conviction calls above."
   Each empty state has an icon + message + CTA button

4. Add error boundaries to each page:
   Create frontend/components/ErrorBoundary.tsx
   Shows: error icon + "Something went wrong" + "Retry" button
   Wrap every page's data-fetching section

5. Mobile responsive improvements:
   - Sidebar: collapse to icon-only on screens < 768px
   - Graph page: full-width on mobile, hide side panel by default
   - Tables: horizontal scroll wrapper on mobile
   - Add viewport meta tag check in layout.tsx

6. Performance: add SWR deduplication and optimistic updates:
   - In BottleneckBoard.tsx: optimistic add when new evidence is ingested
   - In HouseViewNarrative: show stale data while refreshing (not blank)
   - Add revalidateOnFocus: false to slow-changing endpoints (/graph, /entities)

Commit: "feat: frontend showcase hardening — loading skeletons, empty states, error boundaries, mobile responsive"

════════════════════════════════════════════════
PHASE 6 — API RESPONSE CACHING
════════════════════════════════════════════════

Add in-process TTL caching to slow/expensive endpoints so the demo
feels instant for interviewers even without a Redis instance.

1. Create backend/db/cache.py:
   SimpleCache class with:
   - get(key) -> Optional[Any]
   - set(key, value, ttl_seconds: int)
   - invalidate(key)
   - invalidate_prefix(prefix: str)  # e.g. "bottlenecks:" clears all bottleneck keys
   Uses a dict + timestamp, no external dependencies

2. Apply caching to these endpoints:
   - GET /graph/          TTL: 60s  key: "graph:{regime}"
   - GET /bottlenecks/    TTL: 30s  key: "bottlenecks:all"
   - GET /regime/         TTL: 30s  key: "regime:current"
   - GET /regime/timeline TTL: 300s key: "regime:timeline"
   - GET /entities/       TTL: 120s key: "entities:{sector}:{type}:{search}"
   - GET /house-view/narrative TTL: 300s key: "narrative:current" (already cached, verify)
   - GET /models/status   TTL: 10s  key: "models:status"

3. Invalidate relevant cache keys after:
   - POST /evidence/ completes pipeline: invalidate "graph:", "bottlenecks:", "regime:"
   - PUT /house-view/: invalidate "bottlenecks:", "narrative:"

4. Add GET /cache/stats endpoint (dev only) returning cache hit/miss counts

5. Add 3 tests in backend/tests/test_cache.py

Commit: "feat: in-process TTL cache for graph/bottleneck/regime endpoints"

════════════════════════════════════════════════
PHASE 7 — LIVE DEPLOYMENT
════════════════════════════════════════════════

Attempt live deployments to get real public URLs.

1. Try Vercel CLI deployment:
   cd frontend
   npx vercel --prod --yes 2>&1 | tee /tmp/vercel_deploy.log
   cat /tmp/vercel_deploy.log
   If successful: extract URL from output, update README.md Live Demo section
   If auth fails: skip and continue to step 2

2. Try Railway deployment for backend (simpler than Cloud Run, no GCP auth needed):
   Check if railway CLI is available: which railway
   If available:
     railway login --browserless (follow prompts)
     railway init --name ai-transmission-map-backend
     railway up --detach
   If not available: skip

3. If both deployment CLIs are unavailable or fail auth:
   Create infrastructure/DEPLOYMENT_GUIDE.md with step-by-step manual instructions:
   
   ## Option A: Vercel (Frontend, 2 minutes)
   1. Go to vercel.com/new
   2. Import ryker-code/ai-transmission-map
   3. Set Root Directory: frontend
   4. Add env var: NEXT_PUBLIC_API_URL=<your backend URL>
   5. Deploy

   ## Option B: Railway (Backend, 5 minutes)
   1. Go to railway.app/new
   2. Deploy from GitHub: ryker-code/ai-transmission-map
   3. Set root directory: backend
   4. Add env vars from .env.example
   5. Set start command: uvicorn main:app --host 0.0.0.0 --port $PORT

   ## Option C: Render (Free tier, Backend)
   1. Go to render.com/deploy
   2. New Web Service from GitHub
   3. Root directory: backend
   4. Build: pip install -r requirements.txt
   5. Start: uvicorn main:app --host 0.0.0.0 --port $PORT

   ## One-Click Codespaces Demo
   Add badge to README: [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ryker-code/ai-transmission-map)
   This lets anyone launch a fully working dev environment in 60 seconds.

4. Add the Codespaces badge to README.md regardless of whether cloud deploy succeeded

Commit: "feat: deployment guide, Codespaces badge, attempted live deployment"

════════════════════════════════════════════════
PHASE 8 — FINAL INTEGRATION, TESTS, BUILD VERIFICATION
════════════════════════════════════════════════

1. Run full backend test suite: pytest backend/tests/ -v
   Target: 75+ tests passing. Fix any failures.

2. Run frontend build: cd frontend && npm run build
   Target: 12+ pages, 0 TypeScript errors.

3. Update docs/BUILD_LOG.md with Day 5 section:
   - Phases completed
   - New files created
   - Test count (target: 75+)
   - Deployment status
   - Known issues

4. Update docs/INTERVIEW_GUIDE.md:
   - Add scenario branching to technical talking points
   - Add model attribution talking point
   - Add market signals talking point
   - Update demo flow to include the scenario "What if?" feature
     (this is the most impressive live demo moment — highlight it)

5. Update docs/demo_theses.md:
   - Re-run Thesis 1 (Power Constraint) with new 200-entity graph
   - Run scenario branch: "FERC fast-track interconnection approved"
   - Show delta in support/contradiction scores
   - Append scenario output to Thesis 1 section

6. Final commit:
   git add -A
   git commit -m "feat: Day 5 complete — model router, scenario branching, market signals, 200 entities, frontend hardening, caching, deployment guide, 75+ tests"
   git push origin main

════════════════════════════════════════════════
AFTER ALL PHASES: TIME CHECK + DAY 6 PREVIEW
════════════════════════════════════════════════

Run `date`. If before 6:00 AM EDT, proceed to Day 6:

DAY 6 OBJECTIVES (read docs/OVERNIGHT_PROMPT_DAY6.md if it exists, else execute these):

1. BigQuery live connection:
   - Replace SQLite stub with real BigQuery calls for entities, claims, bottleneck_scores
   - Keep SQLite as fallback when BIGQUERY_PROJECT_ID is placeholder
   - Add GET /health/db endpoint reporting which DB is active

2. Streaming API responses:
   - Add POST /memo/stream endpoint using FastAPI StreamingResponse + Server-Sent Events
   - Frontend shows memo text being written character by character
   - Add streaming indicator animation

3. Watchlist feature:
   - GET/POST/DELETE /watchlist/ endpoints
   - Analyst can star entities for quick access
   - Watchlist panel on dashboard showing starred entities with live scores

4. Weekly digest email stub:
   - POST /digest/generate endpoint
   - Generates a weekly summary: regime change, top 3 score movers, new evidence count
   - Output to docs/sample_digest.md as a static example

5. Security hardening:
   - Add API key authentication to all POST/PUT endpoints
   - Header: X-API-Key: {key from .env}
   - Frontend reads from NEXT_PUBLIC_API_KEY env var
   - Add rate limiting (slowapi) to evidence intake endpoints

DO NOT STOP until 6:00 AM EDT or all Day 5 + Day 6 phases are complete.
There are no breaks. Human work schedules do not apply.
