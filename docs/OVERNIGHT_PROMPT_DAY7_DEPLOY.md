# OVERNIGHT_PROMPT_DAY7_DEPLOY.md
# AI Transmission Map — Day 7: Live Deploy + Interview Freeze
# This sprint is the FINAL one. After it completes, the repo is showcase-frozen.
# Start with: claude --dangerously-skip-permissions
# Paste EVERYTHING below into Claude Code

---

You are executing the final sprint of "AI Infrastructure Transmission Map".
The product is feature-complete. This sprint is about:
  1. Getting a real public URL live
  2. Making the demo bulletproof
  3. Writing the interview artifacts
  4. Freezing the showcase state

Run these first:
  git pull origin main
  cat CLAUDE.md
  git log --oneline -5
  cd backend && pip install -r requirements.txt -q
  pytest tests/ -q --tb=short
  cd ../frontend && npm install --silent && npm run build 2>&1 | tail -5

Fix any failures before proceeding.

## Full Build Status (Days 1–6 complete):
- Multi-agent pipeline: Scout→Extractor→Resolver→Critic→Scorer→HouseView (3 LLM models)
- 200 entities, 80 transmission claims, 5 regime types
- 96 backend tests passing, 14+ frontend pages
- All evidence intake: URL, Bloomberg parser, image (Claude vision), voice (Whisper)
- Model router with per-claim LLM attribution
- Scenario branching (What-if thesis workspace with 3 pre-built scenarios)
- Market signals stub wired into scorer
- BigQuery/SQLite dual-mode DB router
- Streaming memo generation (SSE typewriter)
- Watchlist with live score monitoring
- API key auth + slowapi rate limiting on write endpoints
- Weekly digest generator + docs/sample_digest.md
- Multi-analyst stubs, score history sparklines, claim feedback (thumbs up/down)
- TTL cache on all slow endpoints
- Loading skeletons, error boundaries, mobile responsive
- PDF memo export, Regime timeline, Audit trail, House View narrative
- GitHub Actions CI, Codespaces badge, infrastructure/DEPLOYMENT_GUIDE.md
- docs/ARCHITECTURE_DEEP_DIVE.md, docs/INTERVIEW_GUIDE.md, docs/demo_theses.md

## Day 7 Mission: Make it live. Make it airtight. Freeze it.
Execute ALL phases autonomously. After each phase:
  git add -A && git commit -m "[message]" && git push origin main
No permission prompts. No stopping. Fix errors in-place.

════════════════════════════════════════════════
PHASE 1 — PRODUCTION .env AUDIT + .devcontainer
════════════════════════════════════════════════

Ensure any new reviewer or recruiter can run the full product in one command.

1. Audit .env.example — make sure it lists EVERY env var now used in the codebase:
   Run: grep -r 'os.getenv\|os.environ' backend/ --include='*.py' | grep -oP '(?<=")[A-Z_]+(?=")' | sort -u
   Compare against .env.example. Add any missing vars with placeholder values and comments.
   Required vars should include at minimum:
     ANTHROPIC_API_KEY=your-key-here          # Claude Opus for extraction, memo, narrative
     GOOGLE_API_KEY=your-key-here             # Gemini Flash for scouting
     OPENAI_API_KEY=your-key-here             # Whisper for voice transcription
     BIGQUERY_PROJECT_ID=your-project-id      # Optional: use SQLite if not set
     BIGQUERY_DATASET=ai_transmission_map     # Optional
     BIGQUERY_CREDENTIALS_PATH=               # Optional: path to service account JSON
     AITM_API_KEY=dev-key-change-in-production # Auth for write endpoints
     NEXT_PUBLIC_API_URL=http://localhost:8000  # Frontend → backend URL
     NEXT_PUBLIC_API_KEY=dev-key-change-in-production

2. Create/update .devcontainer/devcontainer.json:
   {
     "name": "AI Transmission Map",
     "image": "mcr.microsoft.com/devcontainers/python:3.11",
     "features": {
       "ghcr.io/devcontainers/features/node:1": {"version": "20"}
     },
     "postCreateCommand": "cd backend && pip install -r requirements.txt && cd ../frontend && npm install",
     "postStartCommand": "cd backend && uvicorn main:app --reload --port 8000 &",
     "forwardPorts": [8000, 3000],
     "portsAttributes": {
       "8000": {"label": "FastAPI Backend", "onAutoForward": "notify"},
       "3000": {"label": "Next.js Frontend", "onAutoForward": "openBrowser"}
     },
     "customizations": {
       "vscode": {
         "extensions": ["ms-python.python", "bradlc.vscode-tailwindcss",
                        "esbenp.prettier-vscode", "ms-python.black-formatter"]
       }
     }
   }

3. Add a backend/.env.test file with all-stub values (no real API keys) for CI:
   ANTHROPIC_API_KEY=sk-test-placeholder
   GOOGLE_API_KEY=test-placeholder
   OPENAI_API_KEY=sk-test-placeholder
   BIGQUERY_PROJECT_ID=
   AITM_API_KEY=dev-key-change-in-production
   NEXT_PUBLIC_API_URL=http://localhost:8000
   Verify .github/workflows/ci.yml uses these stub values for pytest.

Commit: "chore: env audit, devcontainer auto-start, CI env vars hardened"

════════════════════════════════════════════════
PHASE 2 — PLAYWRIGHT E2E TESTS (CRITICAL DEMO PATHS)
════════════════════════════════════════════════

Add E2E tests covering the 5 critical demo paths — these run against
the local dev server and catch any regressions before an interview.

1. Install Playwright:
   cd frontend
   npm install -D @playwright/test
   npx playwright install chromium --with-deps

2. Create frontend/playwright.config.ts:
   import { defineConfig } from '@playwright/test';
   export default defineConfig({
     testDir: './e2e',
     use: {
       baseURL: 'http://localhost:3000',
       headless: true,
       screenshot: 'only-on-failure',
     },
     webServer: {
       command: 'npm run dev',
       url: 'http://localhost:3000',
       reuseExistingServer: true,
       timeout: 30000,
     },
   });

3. Create frontend/e2e/critical_paths.spec.ts with these 5 tests:

   test('dashboard loads with stat cards', async ({ page }) => {
     await page.goto('/');
     await expect(page.locator('[data-testid="stat-entity-count"]')).toBeVisible();
     await expect(page.locator('[data-testid="stat-regime"]')).toBeVisible();
   });

   test('graph page renders force graph', async ({ page }) => {
     await page.goto('/graph');
     await expect(page.locator('canvas')).toBeVisible({ timeout: 10000 });
   });

   test('evidence form submits successfully', async ({ page }) => {
     await page.goto('/evidence');
     await page.fill('[data-testid="evidence-url"]', 'https://example.com/test');
     await page.fill('[data-testid="evidence-title"]', 'Test Article');
     await page.selectOption('[data-testid="source-type"]', 'news');
     await page.click('[data-testid="submit-evidence"]');
     await expect(page.locator('[data-testid="evidence-success"]')).toBeVisible({ timeout: 15000 });
   });

   test('thesis run with scenario branch', async ({ page }) => {
     await page.goto('/thesis');
     await page.fill('[data-testid="thesis-text"]',
       'Power constraint will persist for AI infrastructure buildout');
     await page.click('[data-testid="run-thesis"]');
     await expect(page.locator('[data-testid="support-score"]')).toBeVisible({ timeout: 20000 });
     await page.click('[data-testid="scenario-ferc"]');
     await expect(page.locator('[data-testid="scenario-delta"]')).toBeVisible({ timeout: 15000 });
   });

   test('memo generates and streams', async ({ page }) => {
     await page.goto('/memo');
     await page.click('[data-testid="stream-toggle"]');
     await page.click('[data-testid="generate-memo"]');
     await expect(page.locator('[data-testid="memo-cursor"]')).toBeVisible({ timeout: 5000 });
     await expect(page.locator('[data-testid="memo-text"]')).not.toBeEmpty({ timeout: 30000 });
   });

4. Add data-testid attributes to the relevant frontend components for all 5 tests.
   This requires editing: frontend/app/page.tsx, /graph/page.tsx, /evidence/page.tsx,
   /thesis/page.tsx, /memo/page.tsx.

5. Add Playwright run to .github/workflows/ci.yml:
   - name: Run Playwright E2E tests
     run: cd frontend && npx playwright test --reporter=list
     env:
       NEXT_PUBLIC_API_URL: http://localhost:8000

6. Run tests locally: cd frontend && npx playwright test
   Fix any failures. If a test is flaky due to timing, increase timeout.

Commit: "test: Playwright E2E tests for 5 critical demo paths with data-testid attributes"

════════════════════════════════════════════════
PHASE 3 — GRAPH VISUALIZATION UPGRADE
════════════════════════════════════════════════

The graph is the centrepiece visual of the product. Make it interview-worthy.

1. In frontend/components/TransmissionGraph.tsx (or wherever the force-graph lives):

   Node styling:
   - Node size = proportional to bottleneck_score (min 4px, max 24px)
   - Node color by entity_type:
     semiconductor: #6366f1 (indigo)
     utility: #f59e0b (amber)
     hyperscaler: #10b981 (emerald)
     reit: #8b5cf6 (violet)
     equipment: #ef4444 (red)
     financial: #3b82f6 (blue)
     regulatory: #6b7280 (gray)
     default: #94a3b8 (slate)
   - Watched entities (from watchlist): add a gold ring border
   - Top 5 bottleneck nodes: pulsing glow animation

   Edge styling:
   - Edge color by direction:
     bullish: #10b981 (green)
     bearish: #ef4444 (red)
     neutral: #6b7280 (gray)
   - Edge width = confidence * 3 (thin=uncertain, thick=high confidence)
   - Edge label on hover: predicate + confidence% + horizon

   Controls panel (top-right overlay on graph canvas):
   - Regime filter buttons: ALL | AI_CAPEX | SUPPLY_CHAIN | GRID | POWER | REGULATORY
     Clicking filters edges to show only that regime_tag
   - Entity type legend with colored dots
   - "Reset View" button to re-center
   - Node count + edge count display

   Node click action:
   - Right panel slides in (not a new page): shows entity name, score bar,
     top 3 inbound claims, top 3 outbound claims, watchlist star button
   - "Open Full Detail" link to /entities/[id]

2. Add graph export:
   - "Export PNG" button that calls canvas.toDataURL() and triggers download
   - "Export JSON" button that downloads the current filtered graph as
     {nodes: [...], edges: [...], regime_filter: str, exported_at: str}

Commit: "feat: graph visualization upgrade — scored nodes, directional edges, regime filter, slide panel"

════════════════════════════════════════════════
PHASE 4 — LIVE DEPLOYMENT FROM LOCAL MACHINE (INSTRUCTIONS + ATTEMPT)
════════════════════════════════════════════════

This phase prepares everything so deployment takes < 5 minutes from any
machine with Railway/Vercel CLIs installed.

1. Create infrastructure/QUICK_DEPLOY.sh (executable deploy script):
   #!/bin/bash
   set -e
   echo "🚀 AI Transmission Map — Quick Deploy"
   echo "Step 1/4: Installing CLIs..."
   npm install -g @railway/cli vercel 2>/dev/null || true

   echo "Step 2/4: Deploying backend to Railway..."
   cd "$(dirname "$0")/.."
   railway up --detach
   BACKEND_URL=$(railway domain 2>/dev/null | grep https | head -1 | tr -d ' ')
   echo "Backend: $BACKEND_URL"

   echo "Step 3/4: Deploying frontend to Vercel..."
   cd frontend
   NEXT_PUBLIC_API_URL=$BACKEND_URL npx vercel --prod --yes
   FRONTEND_URL=$(cat .vercel/project.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('https://' + d.get('name','') + '.vercel.app')" 2>/dev/null || echo 'Check Vercel dashboard')
   echo "Frontend: $FRONTEND_URL"

   echo "Step 4/4: Smoke test..."
   curl -sf $BACKEND_URL/health | python3 -m json.tool || echo 'Backend not yet ready - check Railway dashboard'
   echo "✅ Deploy complete. Update README with: $FRONTEND_URL"
   chmod +x infrastructure/QUICK_DEPLOY.sh

2. Create railway.json in repo root (for Railway auto-detection):
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {"builder": "NIXPACKS"},
     "deploy": {
       "startCommand": "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 3
     }
   }

3. Create frontend/vercel.json (if not exists or update):
   {
     "buildCommand": "npm run build",
     "outputDirectory": ".next",
     "framework": "nextjs",
     "env": {
       "NEXT_PUBLIC_API_URL": "@next_public_api_url"
     },
     "headers": [
       {"source": "/(.*)",
        "headers": [
          {"key": "X-Content-Type-Options", "value": "nosniff"},
          {"key": "X-Frame-Options", "value": "DENY"},
          {"key": "X-XSS-Protection", "value": "1; mode=block"}
        ]}
     ]
   }

4. Attempt Railway deploy from Codespace:
   npm install -g @railway/cli 2>/dev/null || true
   which railway && railway --version || echo 'Railway CLI not available'
   railway up --detach 2>&1 | tee /tmp/railway_attempt.log || true
   cat /tmp/railway_attempt.log
   # Extract URL if successful
   BACKEND_URL=$(grep -oP 'https://[a-z0-9-]+\.up\.railway\.app' /tmp/railway_attempt.log | head -1 || echo '')
   if [ -n "$BACKEND_URL" ]; then
     echo "SUCCESS: $BACKEND_URL"
     # Update README Live Demo section with real URL
     sed -i "s|https://aitm-backend.up.railway.app|$BACKEND_URL|g" README.md
   fi

5. Attempt Vercel deploy:
   cd frontend
   npx vercel --prod --yes 2>&1 | tee /tmp/vercel_attempt.log || true
   FRONTEND_URL=$(grep 'Production:' /tmp/vercel_attempt.log | awk '{print $2}' | head -1 || echo '')
   if [ -n "$FRONTEND_URL" ]; then
     echo "SUCCESS: $FRONTEND_URL"
     sed -i "s|https://ai-transmission-map.vercel.app|$FRONTEND_URL|g" ../README.md
   fi

Commit: "feat: railway.json, QUICK_DEPLOY.sh, vercel.json security headers, deploy attempt"

════════════════════════════════════════════════
PHASE 5 — DEMO SCRIPT + INTERVIEW VIDEO STORYBOARD
════════════════════════════════════════════════

Create interview artifacts that make the 20-minute technical showcase crisp.

1. Create docs/DEMO_SCRIPT.md — a minute-by-minute live demo walkthrough:

   ## AI Transmission Map — Live Demo Script (18 minutes)

   ### 0:00 — The Pitch (90 seconds)
   Open browser to dashboard. Monologue:
   "This is a multi-agent AI system that maps how AI infrastructure capacity
    constraints transmit through the supply chain — from Nvidia GPU allocation
    through transformer lead times to utility capital plans — and surfaces
    investment thesis support and contradiction scores."

   ### 1:30 — Evidence Ingest (3 minutes)
   1. Go to /evidence. Fill in a Bloomberg URL.
   2. Hit Parse URL — show auto-fill of title + detected entities.
   3. Submit — show the agent pipeline running:
      "Scout (Gemini Flash) → Extractor (Claude Opus) → Resolver → Critic → Scorer"
   4. Show new claim appearing with model attribution badge: "extracted by gemini-2.0-flash"

   ### 4:30 — The Graph (3 minutes)
   1. Go to /graph. Show 200 nodes, color-coded by entity type.
   2. Click regime filter: GRID_BOTTLENECK. Graph highlights relevant edges.
   3. Click a node (e.g., GE Vernova). Slide panel shows score, claims, watchlist star.
   4. Click the gold-bordered node (top bottleneck). Point out pulsing glow.
   5. Hit Export PNG — show download.

   ### 7:30 — Thesis Run + Scenario Branch (5 minutes)
   1. Go to /thesis. Type: "Power constraint moat benefits nuclear and gas peakers"
   2. Run — show support 37.5%, contradiction 12.1%, top 5 bottleneck nodes.
   3. Click "FERC fast-track interconnection approved" scenario button.
   4. Show side-by-side: support drops to ~21%, contradiction rises.
   5. Read the Claude delta narrative aloud.
   "This is the key insight — the analyst can stress-test a thesis in real time
    without mutating the main graph. That’s the 'what-if' workspace."

   ### 12:30 — Streaming Memo (2 minutes)
   1. Go to /memo. Toggle Stream ON.
   2. Hit Generate Memo — show text appearing word by word.
   3. Hit Download PDF when done.

   ### 14:30 — House View + Weekly Digest (2 minutes)
   1. Go to /house-view. Set conviction=HIGH on CEG.
   2. Show narrative regenerates on dashboard.
   3. Go to /digest. Hit Generate — show weekly summary.

   ### 16:30 — Technical Q&A Setup (90 seconds)
   Open docs/ARCHITECTURE_DEEP_DIVE.md in a second tab.
   "Happy to go deep on any of these: scorer design, BigQuery schema,
    multi-model routing rationale, or what v2 would look like."

2. Create docs/ELEVATOR_PITCH.md — three versions:

   ## 30-second version (recruiter screen)
   "I built a multi-agent RAG system that maps AI infrastructure capacity
   constraints as a transmission graph. It ingests evidence from URLs, images,
   and voice, extracts causal claims via Claude and Gemini, scores bottleneck
   nodes using a 5-component weighted algorithm, and lets analysts run
   'what-if' scenario branches on investment theses. 96 tests, 200 entities,
   live streaming memos. Built in 7 days."

   ## 2-minute version (hiring manager)
   [Write a 200-word version covering: problem statement, agent architecture,
    key differentiators (scenario branching, multi-model attribution, streaming),
    technical choices (why LangGraph, why BigQuery, why dual-mode DB),
    build velocity story (6 days from scratch to 96 tests)]

   ## 5-minute version (technical interview)
   [Write a 500-word version including: system design decisions, tradeoffs made,
    what you’d do differently, what production v2 would add,
    and 3 honest known limitations with mitigation plans]

Commit: "docs: DEMO_SCRIPT.md minute-by-minute walkthrough + ELEVATOR_PITCH.md three versions"

════════════════════════════════════════════════
PHASE 6 — FINAL README + SHOWCASE FREEZE
════════════════════════════════════════════════

1. Final README.md rewrite — make it recruiter-grade:

   Structure:
   # AI Infrastructure Transmission Map
   [1-line description]
   [Badges: tests passing | Next.js | FastAPI | Python | BigQuery | Claude | Gemini | Whisper]
   [Open in Codespaces badge] [Deploy to Railway button]

   ## Live Demo
   [Link to frontend URL or "3-minute deploy: see QUICK_DEPLOY.sh"]
   Demo credentials: API key = dev-key-change-in-production

   ## What It Does (3 bullet points max, non-technical)
   ## How It Works (Architecture diagram — keep the ASCII one from Day 3)
   ## Tech Stack table
   ## Project Stats table (96 tests, 14+ pages, 200 entities, 80 claims, 3 models, 4 intake modes)
   ## Quick Start (4 commands to run locally)
   ## API Reference (keep existing, verify all endpoints are listed)
   ## Key Features (keep existing)
   ## Interview Resources (links to DEMO_SCRIPT, ARCHITECTURE_DEEP_DIVE, INTERVIEW_GUIDE)

2. Run final checks:
   pytest backend/tests/ -v 2>&1 | tail -5
   cd frontend && npm run build 2>&1 | tail -5
   python3 backend/scripts/demo_run.py 2>&1 | tail -10

3. Update shield.io test badge count in README to actual passing count.

4. Create a git tag for the showcase version:
   git tag -a v1.0.0-showcase -m "Showcase-ready: 96+ tests, 200 entities, 14+ pages, full agent pipeline"
   git push origin v1.0.0-showcase

5. FREEZE COMMIT — this is the final commit:
   git add -A
   git commit -m "feat: v1.0.0-showcase — graph upgrade, E2E tests, demo script, elevator pitch, final README"
   git push origin main

   Then print to terminal:
   echo ""
   echo "════════════════════════════════════════════"
   echo "✅ AI TRANSMISSION MAP — SHOWCASE FREEZE COMPLETE"
   echo "════════════════════════════════════════════"
   pytest backend/tests/ -q --tb=no | tail -2
   echo "Frontend pages: $(ls frontend/app/**/page.tsx frontend/app/page.tsx 2>/dev/null | wc -l)"
   echo "Git tag: v1.0.0-showcase"
   echo "════════════════════════════════════════════"

════════════════════════════════════════════════
IF ALL 6 PHASES COMPLETE EARLY — OPTIONAL BONUS
════════════════════════════════════════════════

BONUS: OpenAPI spec + Postman collection
- FastAPI auto-generates /openapi.json — verify it’s accurate
- Download it: curl http://localhost:8000/openapi.json > docs/openapi.json
- Create docs/postman_collection.json by converting the OpenAPI spec:
  npx openapi-to-postmanv2 -s docs/openapi.json -o docs/postman_collection.json 2>/dev/null || true
  If converter unavailable, manually write a Postman-format collection with
  the 8 most important endpoints: /health, /graph, /bottlenecks, /evidence (POST),
  /thesis/run (POST), /memo/generate (POST), /regime, /house-view (PUT)
- Add to README: "Import docs/postman_collection.json into Postman to explore the API"
- Commit: "docs: openapi.json + Postman collection for API exploration"

BONUS: Performance benchmark
- Create backend/scripts/benchmark.py:
  Uses httpx to hit 6 endpoints 10x each and report p50/p95/p99 latency
  Endpoints: /health, /graph, /bottlenecks, /regime, /entities, /house-view
  Output: docs/BENCHMARK_RESULTS.md with a markdown table
  Run it: python3 backend/scripts/benchmark.py
- Commit: "perf: benchmark script + results showing p95 < 200ms on cached endpoints"
