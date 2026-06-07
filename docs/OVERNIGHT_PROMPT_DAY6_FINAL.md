# OVERNIGHT_PROMPT_DAY6_FINAL.md
# AI Transmission Map — Day 6 Final Sprint
# This is the LAST planned build sprint before showcase.
# Start with: claude --dangerously-skip-permissions
# Paste EVERYTHING below into Claude Code

---

You are completing the final sprint of "AI Infrastructure Transmission Map".
Run these first before doing anything:
  git pull origin main
  cat CLAUDE.md
  git log --oneline -5
  cd backend && pip install -r requirements.txt -q
  pytest tests/ -q --tb=short
  cd ../frontend && npm install --silent && npm run build 2>&1 | tail -5

Fix any failures before proceeding. Do NOT start new phases if tests are broken.

## Full Build Status (Days 1–5 complete):
- Multi-agent pipeline: Scout(Gemini Flash)→Extractor(Claude Opus)→Resolver→Critic→Scorer→HouseView
- 200 entities, 80 transmission claims, 5 regime types
- 69 backend tests passing, 12+ frontend pages
- All intake: URL, Bloomberg parser, image (vision), voice (Whisper)
- Model router with per-claim attribution
- Scenario branching (What-if thesis workspace)
- Market signals stub wired into 5th scorer component
- TTL cache on all slow endpoints
- Loading skeletons, error boundaries, mobile responsive
- PDF memo export, House View narrative, Regime timeline, Audit trail
- GitHub Actions CI + Vercel deploy workflow
- docs/INTERVIEW_GUIDE.md, docs/demo_theses.md, backend/scripts/demo_run.py
- infrastructure/DEPLOYMENT_GUIDE.md, Codespaces badge

## Day 6 Mission: Production readiness + live deployment
Execute ALL phases autonomously. No permission prompts. No stopping between phases.
After each phase: git add -A && git commit -m "[message]" && git push origin main
Check `date` after each phase — continue until 6:00 PM EDT or all phases done.

════════════════════════════════════════════════
PHASE 1 — BIGQUERY LIVE CONNECTION WITH SQLite FALLBACK
════════════════════════════════════════════════

Upgrade the database layer so real BigQuery is used when credentials are
available, falling back gracefully to SQLite stub for local/Codespace use.

1. Add to backend/requirements.txt:
   google-cloud-bigquery==3.25.0
   google-cloud-bigquery-storage==2.25.0
   db-dtypes==1.3.0

2. Create backend/db/bq_client.py:
   class BigQueryClient:
     def __init__(self):
       - Try to init google.cloud.bigquery.Client(project=config.BIGQUERY_PROJECT_ID)
       - If credentials missing or project is placeholder ("your-project-id"),
         set self.available = False
       - Else set self.available = True

     def query(self, sql: str, params: dict = {}) -> list[dict]:
       - If not available: raise RuntimeError("BigQuery not configured")
       - Execute parameterized query, return list of row dicts

     def insert_rows(self, table: str, rows: list[dict]) -> None:
       - Streaming insert via insert_rows_json

     def table_exists(self, table: str) -> bool

3. Create backend/db/db_router.py:
   class DBRouter:
     """Routes DB calls to BigQuery or SQLite based on availability."""
     def __init__(self):
       self.bq = BigQueryClient()
       self.sqlite = SqliteClient()  # existing stub client
       self.active = "bigquery" if self.bq.available else "sqlite"

     def get_entities(self, sector=None, entity_type=None, search=None) -> list
     def get_claims(self, regime=None, entity_id=None) -> list
     def get_bottleneck_scores(self) -> list
     def upsert_house_view(self, record: dict) -> None
     def insert_evidence(self, record: dict) -> None
     def insert_claim(self, record: dict) -> None

4. Wire DBRouter into all routes that currently call SQLite directly:
   backend/api/routes/entities.py, graph.py, bottlenecks.py,
   evidence.py, house_view.py, claims.py
   Replace direct SQLite calls with db_router.get_*() / db_router.insert_*()

5. Add GET /health/db endpoint:
   Returns: {db_active: "bigquery"|"sqlite", bq_available: bool,
             entity_count: int, claim_count: int, uptime_seconds: float}

6. Add GET /health endpoint (if not exists) returning:
   {status: "ok", version: "1.0.0", db: "bigquery"|"sqlite",
    test_count: 69, entity_count: 200, claim_count: 80}
   This is what recruiters will hit first when checking the live URL.

7. Run pytest -q, fix any failures.
Commit: "feat: BigQuery/SQLite dual-mode DB router with /health/db endpoint"

════════════════════════════════════════════════
PHASE 2 — STREAMING MEMO GENERATION (Server-Sent Events)
════════════════════════════════════════════════

Make memo generation visually impressive by streaming the Claude output
character-by-character in the UI while it's being generated.

Backend:
1. Add POST /memo/stream endpoint in backend/api/routes/memo.py:
   - Accepts same body as POST /memo/generate
   - Returns StreamingResponse with media_type="text/event-stream"
   - Uses claude anthropic streaming API (client.messages.stream())
   - Emits SSE events: data: {"chunk": "text"} as each token arrives
   - Final event: data: {"done": true, "memo_id": "...", "run_id": "..."}
   - On error: data: {"error": "message"}
   - Add Access-Control-Allow-Origin header for CORS

2. Add streaming=True support to memo_agent.py:
   generate_memo_stream(thesis_run: dict, memo_type: str) -> AsyncGenerator[str, None]
   Uses anthropic.AsyncAnthropic().messages.stream() context manager

Frontend:
3. Update frontend/app/memo/page.tsx:
   - Add a "Stream" toggle next to the Generate button
   - When streaming: use EventSource to connect to POST /memo/stream
     (Note: EventSource is GET-only; use fetch with ReadableStream instead)
   - Show memo text appearing word by word with a blinking cursor
   - Typewriter animation: append chunks to a React state string
   - Show "Generating..." spinner with token counter ("247 tokens")
   - Once done: show full memo, enable PDF download button
   - If stream toggle is off: use existing POST /memo/generate (non-streaming)

Commit: "feat: streaming memo generation with SSE typewriter animation"

════════════════════════════════════════════════
PHASE 3 — WATCHLIST FEATURE
════════════════════════════════════════════════

Let the analyst star entities for quick monitoring on the dashboard.

Backend:
1. Create backend/db/watchlist_store.py:
   In-memory set of watched entity_ids (persisted to SQLite watchlist table)
   add(entity_id), remove(entity_id), list() -> list[str], is_watched(entity_id) -> bool

2. Add routes in backend/api/routes/watchlist.py:
   GET  /watchlist/          → list of watched entities with current bottleneck scores
   POST /watchlist/{entity_id}  → add to watchlist
   DELETE /watchlist/{entity_id} → remove from watchlist
   Returns WatchlistEntry: {entity_id, name, ticker, bottleneck_score,
                             score_delta_24h: float, momentum: str, is_watched: bool}
   Register in main.py

3. Add WatchlistEntry schema to schemas.py + TypeScript types

Frontend:
4. Add star/bookmark icon button to:
   - frontend/app/entities/[id]/page.tsx header (toggle watched state)
   - TransmissionGraph.tsx node tooltip (star icon)
   - BottleneckBoard.tsx each row (star icon, grayed if not watched)

5. Add "Watchlist" panel to frontend/app/page.tsx dashboard:
   Below the House View narrative section
   Shows watched entities with: name, ticker, score badge, 24h delta arrow
   "Add to Watchlist" CTA if empty
   Uses SWR with 30s revalidation
   Add Watchlist link to sidebar nav with Bookmark icon

6. Add 3 tests in backend/tests/test_watchlist.py

Commit: "feat: watchlist with starred entities and live score monitoring on dashboard"

════════════════════════════════════════════════
PHASE 4 — API KEY AUTHENTICATION + RATE LIMITING
════════════════════════════════════════════════

Add lightweight security so the live deployment isn’t open to abuse.

Backend:
1. Add to backend/requirements.txt:
   slowapi==0.1.9

2. Create backend/auth.py:
   API_KEY = os.getenv("AITM_API_KEY", "dev-key-change-in-production")

   def verify_api_key(x_api_key: str = Header(None)) -> str:
     if x_api_key != API_KEY:
       raise HTTPException(status_code=401, detail="Invalid API key")
     return x_api_key

   def optional_api_key(x_api_key: str = Header(None)) -> Optional[str]:
     """For read endpoints — key is optional but logged if provided"""
     return x_api_key

3. Apply auth.py:
   - Require verify_api_key on ALL POST, PUT, DELETE endpoints
   - GET endpoints: no auth required (public read access for demo purposes)
   - Add X-API-Key to .env.example and DEPLOYMENT_GUIDE.md

4. Add rate limiting with slowapi:
   - Initialize Limiter(key_func=get_remote_address) in main.py
   - Apply @limiter.limit("10/minute") to POST /evidence/
   - Apply @limiter.limit("30/minute") to POST /thesis/run
   - Apply @limiter.limit("5/minute") to POST /evidence/image and /evidence/voice
   - Apply @limiter.limit("60/minute") to all GET endpoints

5. Update frontend API client (frontend/lib/api.ts or similar):
   - Read API key from process.env.NEXT_PUBLIC_API_KEY
   - Add X-API-Key header to all POST/PUT/DELETE fetch calls
   - Default to "dev-key-change-in-production" if env var not set

6. Update .env.example:
   AITM_API_KEY=dev-key-change-in-production

7. Add 4 tests in backend/tests/test_auth.py:
   - test_post_without_key_returns_401
   - test_post_with_valid_key_returns_200
   - test_get_without_key_returns_200 (GET is public)
   - test_health_endpoint_is_public

Commit: "feat: API key auth on write endpoints + slowapi rate limiting"

════════════════════════════════════════════════
PHASE 5 — WEEKLY DIGEST GENERATOR
════════════════════════════════════════════════

Generate a professional weekly summary that shows the product’s
value as an ongoing monitoring tool, not just a one-time analysis.

Backend:
1. Create backend/tools/digest_generator.py:
   generate_weekly_digest() -> dict with sections:
   {
     week_ending: str (ISO date),
     dominant_regime: str,
     regime_changed: bool,
     top_score_movers: list[{entity, prev_score, curr_score, delta, reason}],
     new_evidence_count: int,
     new_claims_accepted: int,
     top_bottleneck: {entity, score, key_driver},
     falsification_alerts: list[str],  # claims that moved against thesis
     house_view_summary: str,           # 2 sentences from HV narrative
     analyst_calls: list[{entity, conviction, note}]  # high-conviction HV overrides
   }
   Uses real data from claims_store, scorer, regime_detector, house_view_store.

2. Add POST /digest/generate endpoint:
   Calls generate_weekly_digest() then uses Claude claude-opus-4-5 to format it
   as a professional 400-word email-style digest.
   Returns: {digest_text: str, generated_at: str, data: dict}

3. Run generate_weekly_digest() immediately against the current seed data
   and save output to docs/sample_digest.md — this is a showcase artifact.

Frontend:
4. Add frontend/app/digest/page.tsx "Weekly Digest":
   - "Generate Digest" button calling POST /digest/generate
   - Renders formatted digest with section headers
   - Copy-to-clipboard button
   - "Download as PDF" button (reuse pdf_export.py infrastructure)
   - Add Digest link to sidebar nav with Mail icon

Commit: "feat: weekly digest generator with sample output in docs/sample_digest.md"

════════════════════════════════════════════════
PHASE 6 — LIVE DEPLOYMENT (RAILWAY BACKEND + VERCEL FRONTEND)
════════════════════════════════════════════════

Attempt actual live deployment. This is high-priority — a real public URL
is the single most impactful showcase element.

1. Try Railway CLI deployment (backend):
   npm install -g @railway/cli 2>/dev/null || true
   which railway && railway --version
   If available:
     railway login --browserless
     # Follow the browser auth instructions if prompted
     cd /workspaces/ai-transmission-map
     railway init --name aitm-backend 2>&1 | tee /tmp/railway_init.log
     # Create railway.json in root:
     echo '{"build":{"builder":"NIXPACKS"},"deploy":{"startCommand":"cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT","restartPolicyType":"ON_FAILURE"}}' > railway.json
     railway up --detach 2>&1 | tee /tmp/railway_up.log
     cat /tmp/railway_up.log
     railway domain 2>&1 | tee /tmp/railway_domain.log
     BACKEND_URL=$(cat /tmp/railway_domain.log | grep https | head -1 | tr -d ' ')

2. Try Vercel CLI deployment (frontend):
   npm install -g vercel 2>/dev/null || true
   cd frontend
   # Set backend URL from railway or placeholder
   NEXT_PUBLIC_API_URL=${BACKEND_URL:-"https://aitm-backend.up.railway.app"}
   npx vercel --prod --yes \
     --env NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
     2>&1 | tee /tmp/vercel_deploy.log
   FRONTEND_URL=$(cat /tmp/vercel_deploy.log | grep "Production:" | awk '{print $2}')
   echo "Frontend URL: $FRONTEND_URL"

3. If either deployment succeeds:
   - Update README.md with real URLs:
     Replace placeholder with actual live URLs in the "Live Demo" section
   - Add live URL to docs/INTERVIEW_GUIDE.md
   - Run a smoke test: curl $BACKEND_URL/health | python3 -m json.tool
   - If /health returns 200: add a green "Live" badge to README

4. If both fail due to auth (no browser available in Codespace):
   - Create infrastructure/QUICK_DEPLOY.md with the 3-command Railway deploy:
     npm install -g @railway/cli
     railway login
     railway up
   - Note: Run these from your LOCAL machine (not Codespace) where browser auth works
   - Update README "Live Demo" section to say:
     "Run `railway up` from local machine to deploy in 3 minutes. See QUICK_DEPLOY.md."

Commit: "feat: live deployment attempt + QUICK_DEPLOY.md for 3-command deploy"

════════════════════════════════════════════════
PHASE 7 — FINAL TEST SUITE + COMPLETE SHOWCASE POLISH
════════════════════════════════════════════════

1. Run full test suite: pytest backend/tests/ -v
   Target: 85+ tests all passing.
   Write any missing tests for:
   - DB router (test_db_router.py): SQLite fallback, entity count, claim insert
   - Streaming memo (test_memo_stream.py): endpoint returns 200 with text/event-stream
   - Watchlist (test_watchlist.py): already planned in Phase 3
   - Auth (test_auth.py): already planned in Phase 4
   - Digest (test_digest.py): generate_weekly_digest returns all required keys

2. Run frontend build: cd frontend && npm run build
   Target: 14+ pages, 0 TypeScript errors, 0 ESLint errors.

3. Run backend/scripts/demo_run.py and verify it completes without errors.
   If it errors, fix it. This is the first thing a recruiter will run.

4. Final README polish:
   Add a "Project Stats" section near the top:
   | Metric | Value |
   |--------|-------|
   | Backend tests | 85+ passing |
   | Frontend pages | 14+ |
   | Entities in graph | 200 |
   | Transmission claims | 80 |
   | Agent models | 3 (Claude Opus, Gemini Flash, Whisper) |
   | Evidence intake modes | 4 (URL, Image, Voice, Bloomberg) |
   | API endpoints | 20+ |

5. Add docs/ARCHITECTURE_DEEP_DIVE.md:
   A 3-page technical deep dive for engineering interviews:
   - Why LangGraph for the agent pipeline (vs raw chains)
   - Why BigQuery for the graph store (vs Neo4j / PostgreSQL)
   - The 5-component scorer design decisions
   - Why house view is a separate agent layer (not just a weight in scorer)
   - The TTL cache design (why not Redis for this use case)
   - Multi-model routing rationale (cost vs accuracy tradeoff)
   - What would change in a production v2 (streaming graph updates,
     real-time price feed, user authentication, multi-analyst collaboration)

6. Update docs/INTERVIEW_GUIDE.md final version:
   - Add live URL (or Codespaces URL) as the demo link
   - Add "Architecture Deep Dive" reference for engineering interviews
   - Add 3 expected hard questions + model answers:
     Q: "Why not just use a vector DB for the claims?"
     Q: "How does the scorer handle conflicting evidence?"
     Q: "What would you change if you had 6 months instead of 6 days?"

7. Final commit:
   git add -A
   git commit -m "feat: Day 6 complete — BigQuery dual-mode, streaming memo, watchlist, auth/rate-limit, weekly digest, 85+ tests, architecture deep dive"
   git push origin main

════════════════════════════════════════════════
IF PHASES 1-7 COMPLETE BEFORE 6 PM EDT — BONUS PHASE
════════════════════════════════════════════════

BONUS A: Multi-analyst collaboration stubs
- Add user_id: str field to HouseViewCreate and ClaimCreate schemas
- Add GET /analysts/ endpoint listing unique user_ids from house_view and claims tables
- Add author attribution on BottleneckBoard rows and entity detail pages
- This shows the product is designed for teams, not just solo analysts

BONUS B: Score history tracking
- Create backend/db/score_history.py: append bottleneck scores with timestamp to
  score_history.jsonl on every scorer run
- Add GET /entities/{id}/score-history endpoint returning last 30 snapshots
- Add mini sparkline chart on entity detail page using CSS-only bars
  (no chart lib — width = score percentage, Tailwind height-2 bars in a row)

BONUS C: Claim confidence calibration
- Add POST /claims/{claim_id}/feedback endpoint:
  body: {analyst_verdict: "confirm"|"reject"|"uncertain", note: str}
  Updates claim confidence: confirm += 0.05 (max 0.95), reject -= 0.10 (min 0.10)
  Triggers scorer re-run for affected entities
- Add quick verdict buttons (thumbs up/down) on audit trail panel

Commit each bonus separately with descriptive messages.

DO NOT STOP until 6:00 PM EDT or all phases + bonuses are complete.
