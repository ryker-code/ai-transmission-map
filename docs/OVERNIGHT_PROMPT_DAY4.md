# OVERNIGHT_PROMPT_DAY4.md
# AI Transmission Map — Day 4 Autonomous Execution Prompt
# Start with: claude --dangerously-skip-permissions
# Then paste EVERYTHING below this line into Claude Code

---

You are continuing the build of "AI Infrastructure Transmission Map".
Read CLAUDE.md before doing anything else. Then run `git pull origin main`
to ensure you have the latest code.

## Current Build Status (as of Day 3 completion)
- Day 1 COMPLETE: repo, schemas, stubs, seed data (100 entities, 30 claims), frontend shell
- Day 2 COMPLETE: LangGraph orchestrator (Scout→Extractor→Resolver→Critic→Scorer),
  real graph/bottleneck/thesis/memo routes, TransmissionGraph.tsx, BottleneckBoard.tsx,
  regime_detector.py, evidence ingest page, house view page + UI, BigQuery DDL
- Day 3 COMPLETE: full 5-component weighted scorer, standalone EntityResolver,
  house_view agent with conviction bonuses, Bloomberg URL parser + Parse button,
  multimodal image intake (Claude vision), 3 polished demo theses with live API output,
  Vercel deploy config, Cloud Run Dockerfile, polished README with badges + ASCII diagram
- 42/42 backend tests passing. 7 Next.js routes building cleanly.

## What remains (your mission today):
1. Live Vercel deployment — public URL for recruiter showcase
2. Voice note intake — audio file → transcription → claim extraction
3. Entity detail pages — /entities/[id] drill-down with full claim history
4. Regime timeline — visual history of regime_tag shifts over evidence dates
5. Audit trail UI — every graph edge traceable to source evidence in the UI
6. PDF export — memo download as formatted PDF
7. House view analyst narrative — "your viewpoint" section on dashboard

Execute ALL phases below autonomously. Do not ask for permission.
If ambiguous, pick conservative interpretation and add TODO comment.
If a command fails, retry once, document in docs/known_issues.md, continue.
Check time with `date` after each phase. If before 6:00 AM EDT, continue to next phase.
After every phase, git commit with a descriptive message and push to main.

════════════════════════════════════════════════
PHASE 1 — LIVE VERCEL DEPLOYMENT
════════════════════════════════════════════════

Deploy the frontend to Vercel so there is a real public URL.

1. Run: cd frontend && npx vercel --prod --yes
   If it asks for project linking, accept all defaults (link to ryker-code/ai-transmission-map).
   If login is required and cannot be completed non-interactively, skip to Phase 1b.

1b. FALLBACK if Vercel CLI auth fails:
   - Create frontend/.vercel/project.json stub:
     { "orgId": "ryker-code", "projectId": "ai-transmission-map" }
   - Update README.md "Live Demo" section with:
     "Deploy instantly: click the Deploy to Vercel button above.
      Set NEXT_PUBLIC_API_URL to your Cloud Run backend URL."
   - Add GitHub Actions workflow .github/workflows/deploy.yml:
     name: Deploy to Vercel
     on:
       push:
         branches: [main]
     jobs:
       deploy:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - uses: actions/setup-node@v4
             with:
               node-version: '20'
           - run: cd frontend && npm ci && npm run build
           - name: Deploy to Vercel
             uses: amondnet/vercel-action@v25
             with:
               vercel-token: ${{ secrets.VERCEL_TOKEN }}
               vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
               vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
               working-directory: ./frontend
               vercel-args: '--prod'

2. Add GitHub Actions CI workflow .github/workflows/ci.yml:
   name: CI
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install -r backend/requirements.txt
         - run: pytest backend/tests/ -v
         - uses: actions/setup-node@v4
           with:
             node-version: '20'
         - run: cd frontend && npm ci && npm run build

3. Commit: "ci: add GitHub Actions CI + Vercel deploy workflow"

════════════════════════════════════════════════
PHASE 2 — VOICE NOTE INTAKE
════════════════════════════════════════════════

Add voice/audio evidence intake using OpenAI Whisper API for transcription
then Claude for claim extraction from transcript.

Backend:
1. Add to backend/requirements.txt:
   openai==1.30.0
   (for Whisper API access — use openai.Audio.transcriptions)

2. Create backend/tools/voice_intake.py:
   - transcribe_audio(audio_bytes: bytes, filename: str) -> str:
     Uses OpenAI Whisper API (model="whisper-1") to transcribe
     Falls back to stub transcript if OPENAI_API_KEY is placeholder
   - extract_claims_from_transcript(transcript: str, analyst_context: str) -> list[dict]:
     Uses Claude claude-opus-4-5 to extract structured transmission claims from transcript
     Same JSON schema as image_intake.py claim extraction
     Prompt: "You are analyzing a spoken analyst note about AI infrastructure.
     Extract transmission claims between entities. Output JSON array."
   - Full pipeline: audio → transcribe → extract_claims → critic → scorer

3. Add POST /evidence/voice endpoint in backend/api/routes/evidence.py:
   - Accepts multipart/form-data: audio (file, max 25MB), analyst_context (str, required)
   - Supported formats: .mp3, .mp4, .wav, .m4a, .webm
   - Returns EvidenceResponse with transcript field added
   - Add transcript: Optional[str] field to EvidenceResponse schema

4. Add test backend/tests/test_voice_intake.py:
   - test_transcribe_stub(): with placeholder API key, returns stub transcript
   - test_voice_endpoint_accepts_wav(): POST with minimal WAV bytes, expect 200

Frontend:
5. Add "Record Voice Note" section to frontend/app/evidence/page.tsx:
   - Browser MediaRecorder API to record from microphone
   - Record button (red when recording), Stop button, Play back preview
   - analyst_context textarea (required)
   - Upload to POST /evidence/voice
   - Show transcript after processing, then extracted claims preview
   - Fallback: file upload picker for .mp3/.wav if microphone unavailable

════════════════════════════════════════════════
PHASE 3 — ENTITY DETAIL PAGES
════════════════════════════════════════════════

Build drill-down pages for every entity in the graph.

Backend:
1. Add GET /entities/{entity_id} route returning:
   - Entity metadata (name, type, sector, ticker)
   - All claims where entity is subject OR object (inbound + outbound)
   - Current bottleneck score + all 5 components
   - House view status (weight, conviction, analyst_note)
   - Top 3 related entities by claim count
   Add EntityDetailResponse schema to backend/api/schemas.py

Frontend:
2. Create frontend/app/entities/[id]/page.tsx:
   - Header: entity name, type badge (color-coded), ticker if public, sector
   - Bottleneck Score card: large score number, 5-component breakdown as horizontal bars
   - "Outbound Claims" table: predicate | target entity | direction | confidence | horizon
   - "Inbound Claims" table: source entity | predicate | direction | confidence | horizon
   - "House View" card: conviction badge, weight slider display, analyst note
   - "Related Entities" row: 3 entity cards linking to their detail pages
   Dark theme consistent with rest of app.

3. Make graph nodes in TransmissionGraph.tsx clickable:
   On node click, navigate to /entities/[id] instead of just showing side panel
   Keep side panel as quick preview, add "View Full Detail →" link

4. Add entity search to the nav sidebar:
   Small search input at bottom of sidebar
   Queries GET /entities?search=term (add search param to entities route)
   Shows dropdown of matching entity names, clicking navigates to detail page

════════════════════════════════════════════════
PHASE 4 — REGIME TIMELINE
════════════════════════════════════════════════

Build a visual timeline showing how the dominant regime has evolved
as evidence has been ingested over time.

Backend:
1. Add GET /regime/timeline endpoint returning list of:
   { date: str, dominant_regime: str, regime_scores: dict, evidence_count: int }
   Simulate 30-day history using seed claim dates and regime detection logic
   Add RegimeTimelineEntry schema to schemas.py

Frontend:
2. Create frontend/app/regime/page.tsx "Regime Timeline":
   - Title: "Market Regime History"
   - Timeline visualization using a simple CSS/div-based horizontal timeline
     (no external chart lib needed — use Tailwind width percentages)
   - Each regime period shown as a colored band:
     AI_CAPEX_EXPANSION = indigo, SUPPLY_CHAIN_STRESS = amber,
     GRID_BOTTLENECK = red, POWER_PRICE_SPREAD = green, REGULATORY = purple
   - Hovering a period shows: regime name, date range, dominant evidence count,
     top 3 bottleneck nodes during that period
   - Current regime highlighted with pulsing border animation
   - Below timeline: "Regime Transition Signals" list — what evidence patterns
     indicate a regime shift may be occurring

3. Add Regime Timeline to nav sidebar with TrendingUp icon

════════════════════════════════════════════════
PHASE 5 — AUDIT TRAIL UI
════════════════════════════════════════════════

Make every graph edge and bottleneck score traceable to its source evidence
directly in the UI, so an investor can answer "why does this claim exist?"

Backend:
1. Add GET /claims/{claim_id}/evidence endpoint returning:
   - The claim details
   - All source_documents and evidence_notes linked to this claim
   - The critic's accept/reject reasoning (from critic agent output)
   - Which agent created it (extractor version, timestamp)
   Add ClaimAuditResponse schema

2. Enhance GET /graph/ to include claim_id on each edge (already in GraphEdge? if not, add it)

Frontend:
3. In TransmissionGraph.tsx, make edges clickable:
   On edge click, fetch GET /claims/{claim_id}/evidence
   Show audit panel on right side:
   - Claim statement in plain English ("Nvidia supplies GPU Clusters")
   - Confidence score + direction
   - Source evidence list: each with URL, analyst note snippet, trust score
   - Critic verdict: "Accepted — causal logic score 0.87, corroborated by 2 sources"
   - Timestamp + agent version

4. In BottleneckBoard.tsx, make the "top_evidence" snippets clickable:
   Clicking opens same audit panel for that specific claim

════════════════════════════════════════════════
PHASE 6 — PDF MEMO EXPORT
════════════════════════════════════════════════

Add PDF export so memos can be downloaded as formatted documents
for interview portfolio and investor presentations.

Backend:
1. Add to backend/requirements.txt:
   reportlab==4.1.0

2. Create backend/tools/pdf_export.py:
   - generate_memo_pdf(memo: MemoResponse, thesis: str) -> bytes:
     Creates a formatted PDF using reportlab
     Layout:
       Page 1: Header "AI Infrastructure Transmission Map" logo text,
               date, regime badge, thesis statement
       Page 2: Memo sections (Regime, Bottleneck, Chain, Names, Falsifiers, House View)
               Each section with bold heading, body text, confidence indicators
       Page 3: Top 10 bottleneck nodes table with scores and components
     Uses dark-on-light professional style, not dark theme
     Adds footer: "Generated by AI Transmission Map | Analyst Tool | Not Investment Advice"

3. Add GET /memo/{memo_id}/pdf endpoint:
   - Returns PDF as StreamingResponse with content-type application/pdf
   - Filename: aitm-memo-{memo_id[:8]}-{date}.pdf

Frontend:
4. Add "Download PDF" button to frontend/app/memo/page.tsx:
   Calls GET /memo/{memo_id}/pdf
   Uses browser download via anchor[download] trick
   Show loading spinner while generating

5. Add "Export to PDF" to thesis run results on frontend/app/thesis/page.tsx:
   After a thesis run completes and memo is generated, show PDF download button

════════════════════════════════════════════════
PHASE 7 — HOUSE VIEW ANALYST NARRATIVE
════════════════════════════════════════════════

Add a "House View" narrative section to the dashboard that surfaces
YOUR analytical perspective as the investor — this is the key differentiator
showing the product reflects human judgment, not just model output.

Backend:
1. Add GET /house-view/narrative endpoint:
   - Reads all house_view records with high/medium conviction
   - Uses Claude claude-opus-4-5 to generate a 3-paragraph analyst narrative:
     Para 1: What the current graph says about the regime (data-driven)
     Para 2: Where the analyst's house view diverges from model consensus
     Para 3: Top 2-3 highest-conviction calls with brief rationale
   - Cache for 5 minutes to avoid repeated API calls
   - Returns: { narrative: str, generated_at: str, conviction_count: int }

Frontend:
2. Add "House View" section to frontend/app/page.tsx dashboard (below stat cards):
   - Section heading: "Analyst House View" with Star icon
   - Three-paragraph narrative rendered with proper typography
   - "Last updated" timestamp + "Refresh" button
   - Conviction summary: "3 High | 2 Medium | 1 Low" badges
   - "Edit House View →" link to /house-view page

════════════════════════════════════════════════
PHASE 8 — FINAL INTEGRATION + SHOWCASE POLISH
════════════════════════════════════════════════

1. Run full test suite: pytest backend/tests/ -v
   Fix any failures. Target: 50+ tests all passing.

2. Run frontend build: cd frontend && npm run build
   Fix any TypeScript errors. Ensure all 9+ pages build cleanly.

3. Add "Quick Demo" script backend/scripts/demo_run.py:
   - Seeds the backend with 5 high-quality evidence notes about current AI infra themes
   - Runs all 3 demo theses from docs/demo_theses.md through the API
   - Prints a formatted summary of results
   - Usage: python backend/scripts/demo_run.py
   This lets you demo the product instantly in an interview without live data entry.

4. Update docs/demo_theses.md with refreshed API output from the 5-component scorer
   (the Day 3 output used heuristic scores — re-run with the real scorer now)

5. Create docs/INTERVIEW_GUIDE.md:
   A 2-page guide for using this project in interviews:
   - 30-second elevator pitch for the project
   - 5 technical talking points (LangGraph architecture, multi-agent design,
     BigQuery graph modeling, multimodal intake, house view agent)
   - 3 business talking points (investor thesis interrogation, bottleneck scoring,
     transmission chain mapping)
   - How to run a live demo in 5 minutes during an interview
   - Questions you can answer about design decisions

6. Update README.md:
   - Add "Interview Showcase" section with the elevator pitch
   - Add "Technical Highlights" section listing the agent pipeline,
     model roster (Claude Opus, Gemini Flash, Whisper), and key design decisions
   - Ensure the Deploy to Vercel button is prominent at top

7. Final git commit:
   git add -A
   git commit -m "feat: Day 4 complete — voice intake, entity pages, regime timeline, audit trail, PDF export, house view narrative, CI/CD, interview guide"
   git push origin main

════════════════════════════════════════════════
AFTER ALL PHASES: TIME CHECK
════════════════════════════════════════════════

Run `date`. If before 6:00 AM EDT, proceed to Day 5 tasks:

DAY 5 OBJECTIVES (if time permits after Day 4):

1. Microsoft AI / Gemma 4 integration — add a model comparison feature:
   Create backend/tools/model_router.py that routes extraction tasks to
   different models based on claim complexity:
   - Simple entity extraction → Gemini 2.0 Flash (fast, cheap)
   - Complex causal reasoning → Claude claude-opus-4-5 (accurate)
   - Structured JSON output → Gemma 4 via Google AI API if available
   Add a GET /models/status endpoint showing which models are active
   Add model attribution to each claim (which model extracted it)
   Add model comparison UI: frontend/app/models/page.tsx showing
   extraction accuracy by model across claim types

2. Scenario branching in thesis workspace:
   After a thesis run, add "What if?" scenario buttons:
   - "What if transformer lead times normalize to 52 weeks?"
   - "What if FERC approves fast-track interconnection reform?"
   - "What if a major hyperscaler pauses capex?"
   Each scenario re-runs the thesis with modified claim weights
   Show side-by-side support/contradiction score comparison

3. Live market signal stub:
   Create backend/tools/market_signals.py with placeholder functions
   that would connect to a price feed:
   - get_relative_performance(ticker, benchmark, days) → float
   - get_sector_momentum(sector) → dict
   Currently returns mock data with clear TODO for live feed connection
   Wire market_confirmation component of scorer to use this
   Show "Market Signals" card on entity detail pages

DO NOT STOP until 6:00 AM EDT or all Day 4 + Day 5 phases are complete.
There are no breaks. Human work schedules do not apply.
