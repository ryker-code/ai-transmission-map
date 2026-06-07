# OVERNIGHT_PROMPT_DAY3.md
# AI Transmission Map — Day 3 Autonomous Execution Prompt
# Run this after rate limit resets (~3:48 AM EDT)
# Start with: claude --dangerously-skip-permissions
# Then paste EVERYTHING below this line into Claude Code

---

You are continuing the build of "AI Infrastructure Transmission Map".
Read CLAUDE.md before doing anything else.
The repo is at: https://github.com/ryker-code/ai-transmission-map

## Current Build Status (as of Day 2 completion)
- Day 1 COMPLETE: repo, schemas, stubs, seed data (100 entities, 30 claims), frontend shell
- Day 2 COMPLETE: LangGraph orchestrator (Scout→Extractor→Resolver→Critic→Scorer), 
  real graph/bottleneck/thesis routes, TransmissionGraph.tsx, BottleneckBoard.tsx,
  memo_agent.py (Claude Opus), regime_detector.py, evidence ingest page,
  house view page + UI, BigQuery DDL migrations 001 + 002
- All 8/8 backend tests passing. 7 Next.js routes building cleanly.

## What is NOT yet done (your mission today):
1. scorer.py — full 5-component weighted bottleneck scorer (not just heuristic)
2. resolver.py — standalone entity resolution agent
3. house_view agent — backend that applies house view weights to bottleneck scores
4. Bloomberg evidence URL parser — extract real metadata from bloomberg.com URLs
5. Image ingestion — multimodal chart/slide intake via Claude vision
6. Vercel deployment — public frontend URL
7. Cloud Run deployment — public backend URL
8. 3 demo theses — polished interview-ready thesis runs saved to docs/demo_theses.md
9. README polish — architecture diagram, live demo badge, tool badges

Execute ALL phases below autonomously. Do not ask for permission. 
If ambiguous, pick conservative interpretation and add TODO comment.
If a command fails, retry once, document in docs/known_issues.md, continue.
Check time with `date` after each phase. If before 6:00 AM EDT, continue to next phase.
After every phase, git commit with a descriptive message and push to main.

════════════════════════════════════════════════
PHASE 1 — FULL WEIGHTED SCORER (replace heuristic)
════════════════════════════════════════════════

Replace the heuristic scorer in backend/agents/critic.py (or wherever 
scoring currently lives) with a proper standalone backend/agents/scorer.py.

The scorer must compute bottleneck_score as a weighted sum of 5 components:

  evidence_intensity    × 0.30   (count of accepted claims touching this node)
  recency_score         × 0.20   (exponential decay: score = e^(-days_since_last_claim/30))
  cross_source_agreement × 0.25  (fraction of claims corroborated by 2+ sources)
  market_confirmation   × 0.15   (placeholder: 0.5 default; note as TODO for live price feed)
  house_view_weight     × 0.10   (load from house_view table; default 1.0 if not set)

Implementation requirements:
- Create backend/agents/scorer.py with a compute_bottleneck_scores(entity_ids: list) function
- Load all accepted claims from the SQLite stub (backend/db/local/aitm_stub.db)
- For each entity, compute all 5 components and the weighted sum
- Normalize final scores to 0-100 range
- Write results to bottleneck_scores table (or update in-memory store if BQ not available)
- Return sorted list of BottleneckEntry objects matching the schema in backend/api/schemas.py
- Update GET /bottlenecks/ route to call this scorer instead of the heuristic
- Add test: test_scorer_returns_ranked_list() in backend/tests/test_scorer.py

════════════════════════════════════════════════
PHASE 2 — STANDALONE ENTITY RESOLVER
════════════════════════════════════════════════

Create backend/agents/resolver.py with an EntityResolver class.

Requirements:
- Load all canonical entities from seed data (backend/db/seed_data/entities.json)
- Build an alias index: maps every alias and ticker to canonical entity id
- resolve(name: str) -> Optional[dict]: fuzzy-match input name against canonical names
  and aliases using simple substring + lowercase normalization (no external fuzzy lib needed)
- resolve_batch(names: list[str]) -> dict[str, Optional[dict]]: batch resolution
- merge_duplicate(entity_a_id, entity_b_id): mark one as alias of the other in the store
- Wire into the extractor pipeline: after claim extraction, resolve all entity names 
  before creating claims, so "NVDA", "Nvidia Corp", "Nvidia" all resolve to the same node
- Add test: test_resolver_canonical() in backend/tests/test_resolver.py

════════════════════════════════════════════════
PHASE 3 — HOUSE VIEW AGENT (backend weight application)
════════════════════════════════════════════════

Create backend/agents/house_view.py with an apply_house_view(scores: list) function.

Requirements:
- Load house_view records from the SQLite stub
- For each bottleneck score, look up if the entity has a house_view weight_override
- Multiply the house_view_weight component by the override (clamp to 0.1-3.0)
- If conviction = "high", add 0.10 bonus to final score (before normalization)
- If conviction = "low", subtract 0.10 from final score (floor at 0)
- Apply pinned_thesis: if set, add entity to a "pinned" list returned alongside scores
- Update PUT /house-view/ route to persist to SQLite stub AND trigger a scorer re-run
- Return updated BottlenecksResponse with house view adjustments visible in components dict
- Add test: test_house_view_weight_applied() in backend/tests/test_house_view.py

════════════════════════════════════════════════
PHASE 4 — BLOOMBERG EVIDENCE URL PARSER
════════════════════════════════════════════════

Create backend/tools/bloomberg_parser.py with a BloombergParser class.

Requirements:
- parse_url(url: str) -> dict: extracts metadata from a bloomberg.com URL
  - title: from URL path slug (convert hyphens to spaces, title-case)
  - topic_tags: infer from URL path segments 
    (e.g. /news/articles/ → "news", /technology/ → "technology", /energy/ → "energy")
  - source_type: always "bloomberg"
  - estimated_date: extract from URL if present (bloomberg URLs often contain YYYY-MM-DD)
  - access_class: always "metadata_only" (we store no article body)
- extract_entities_from_title(title: str) -> list[str]: 
  run title through the resolver to find matching canonical entity names
  Return only entities that match with >0.7 confidence
- This is intentionally lightweight — we respect bloomberg.com's ToS by 
  storing only URL metadata and analyst-written paraphrases, never article content
- Update POST /evidence/ route: if source_type="bloomberg", auto-run parse_url 
  to enrich the source_document record before pipeline triggers
- Update the evidence ingest form (frontend/app/evidence/page.tsx):
  add a "Parse URL" button that calls a new GET /evidence/parse-url?url= endpoint
  and auto-fills the title and tags fields
- Add test: test_bloomberg_url_parser() in backend/tests/test_bloomberg_parser.py
  with 5 example bloomberg URLs

════════════════════════════════════════════════
PHASE 5 — IMAGE INGESTION (multimodal)
════════════════════════════════════════════════

Add image-based evidence intake using Claude's vision capability.

Backend:
- Create backend/tools/image_intake.py with extract_claims_from_image(image_bytes, 
  analyst_context: str) -> list[dict] function
- Use Claude claude-opus-4-5 with vision: send image + prompt asking it to identify 
  transmission claims visible in the chart/diagram/slide
- Prompt must instruct Claude to output JSON array of claims matching ClaimCreate schema
- Add POST /evidence/image endpoint accepting multipart/form-data with:
  - image: file upload (PNG/JPG/PDF first page)  
  - analyst_context: str (required — what is this chart about?)
  - source_url: str (optional bloomberg or public URL)
- Store the extracted claims through the same critic → scorer pipeline
- Add test with a stub image (1x1 white PNG encoded as base64)

Frontend:
- Add an "Upload Chart/Slide" section to frontend/app/evidence/page.tsx
- File picker accepting .png .jpg .pdf
- analyst_context textarea (required before upload)
- Show extracted claims preview after upload before confirming

════════════════════════════════════════════════
PHASE 6 — THREE DEMO THESES
════════════════════════════════════════════════

Create docs/demo_theses.md with 3 complete investment theses 
that showcase the product's full capability for job interviews.

For each thesis:
1. Write the thesis statement (2-3 sentences, investor-grade language)
2. Run POST /thesis/run against the live backend (use httpx or curl) 
   with depth=3 and capture the JSON response
3. Write the supporting claims narrative (use actual output from the API)
4. Write the contradicting claims section
5. Write falsification triggers
6. Write a 200-word buyside investor memo using the memo agent
7. Note which bottleneck nodes are most exposed

Thesis 1 — Power Constraint Thesis:
"US utilities with existing nuclear generation capacity and signed 
data center interconnection agreements are structurally underpriced 
relative to the duration and scale of AI infrastructure build-out. 
Grid interconnection queues and transformer shortages create a 
multi-year moat for companies with existing clean firm power. 
Primary names: Constellation Energy, Vistra Corp, Talen Energy."

Thesis 2 — Thermal Management Thesis:
"The shift to 1000W+ GPU racks creates a step-change in cooling 
infrastructure demand that liquid cooling vendors cannot satisfy 
at current production scale. Vertiv and Eaton are capacity-
constrained beneficiaries while traditional air-cooling REITs 
face retrofitting costs that will compress data center operator 
margins through 2027."

Thesis 3 — Transmission Equipment Thesis:
"US power transformer lead times exceeding 100 weeks represent 
the single most underappreciated bottleneck in the AI 
infrastructure build-out. GE Vernova and Hitachi Energy are 
capacity-constrained, creating a durable pricing advantage 
while creating second-order risk for data center developers 
relying on grid interconnection timelines in PJM and MISO 
territories."

After writing all 3, run each through the API and append actual 
API output (support_score, contradiction_score, top 3 exposed entities,
top 2 falsification triggers) to each thesis section.

════════════════════════════════════════════════
PHASE 7 — VERCEL DEPLOYMENT
════════════════════════════════════════════════

Deploy the frontend to Vercel for a public showcase URL.

1. Create frontend/vercel.json:
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://aitm-backend-placeholder.run.app"
  }
}

2. Update frontend/next.config.ts to allow image domains and set 
   output = "standalone" for Cloud Run compatibility

3. Create infrastructure/cloud_run/Dockerfile:
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY .env.example .env
EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]

4. Create infrastructure/cloud_run/cloudbuild.yaml for GCP Cloud Build

5. Update README.md with:
   - Add "Deploy to Vercel" button: [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ryker-code/ai-transmission-map)
   - Add tech stack badges using shields.io
   - Add a "Live Demo" section with placeholder URL
   - Add "Architecture" section with ASCII diagram from docs/architecture.md inlined
   - Add "Demo Theses" section linking to docs/demo_theses.md

════════════════════════════════════════════════
PHASE 8 — FINAL POLISH AND TEST SUITE EXPANSION
════════════════════════════════════════════════

1. Run full test suite: pytest backend/tests/ -v
   Fix any failures. Target: 12+ tests all passing.

2. Run frontend build: cd frontend && npm run build
   Fix any TypeScript errors or warnings.

3. Add these missing tests if not already present:
   - test_thesis_run_returns_falsifiers()
   - test_memo_generates_text()  
   - test_regime_detector_returns_dominant()
   - test_house_view_weight_applied()
   - test_scorer_returns_ranked_list()
   - test_resolver_canonical()
   - test_bloomberg_url_parser()

4. Update docs/BUILD_LOG.md:
   - Day 3 completion timestamp
   - All new files created
   - Test results (pass/fail counts)
   - Deployment URLs (or "pending" if not yet live)
   - Known issues
   - Day 4 objectives

5. Final git commit and push:
   git add -A
   git commit -m "feat: Day 3 complete — scorer, resolver, house view agent, Bloomberg parser, image intake, 3 demo theses, Vercel deploy config"
   git push origin main

════════════════════════════════════════════════
AFTER ALL PHASES: TIME CHECK
════════════════════════════════════════════════

Run `date`. If before 6:00 AM EDT, proceed to Day 4 tasks:

DAY 4 OBJECTIVES (if time permits after Day 3):
1. Voice note intake: add POST /evidence/voice endpoint accepting audio file,
   transcribe with whisper or Google Speech-to-Text, extract claims from transcript
2. Regime timeline: build a timeline view showing how regime_tag has changed 
   over ingested evidence dates (frontend component: app/regime/page.tsx)
3. Entity detail pages: app/entities/[id]/page.tsx showing all claims 
   touching that entity, bottleneck score history, house view status
4. Export: add GET /export/thesis/{run_id}.pdf that generates a PDF memo
   using reportlab or weasyprint
5. Live Vercel deployment: run `npx vercel --prod` from the frontend directory

DO NOT STOP until 6:00 AM EDT or all Day 3 + Day 4 phases are complete.
There are no breaks. Human work schedules do not apply.
