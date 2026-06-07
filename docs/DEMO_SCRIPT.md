# AI Transmission Map — Live Demo Script (18 minutes)

## Pre-demo checklist
- [ ] Backend running: `cd backend && uvicorn main:app --reload --port 8000`
- [ ] Frontend running: `cd frontend && npm run dev`
- [ ] Browser open to `http://localhost:3000`
- [ ] `docs/ARCHITECTURE_DEEP_DIVE.md` open in a second tab
- [ ] API key set: `curl http://localhost:8000/health`

---

## 0:00 — The Pitch (90 seconds)

Open browser to dashboard (`/`). Monologue:

> "This is a multi-agent AI system that maps how AI infrastructure capacity
> constraints transmit through the supply chain — from Nvidia GPU allocation
> through transformer lead times to utility capital plans — and surfaces
> investment thesis support and contradiction scores.
>
> It's purpose-built for one workflow: an analyst has a thesis like
> 'power constraint benefits nuclear operators' — and they want to know how
> strongly the evidence graph supports or contradicts it, in real time."

Point to the stat cards: entities, claims, regime, bottleneck score.

---

## 1:30 — Evidence Ingest (3 minutes)

1. Navigate to `/evidence`.
2. Fill in a Bloomberg or Reuters URL in the URL field.
3. Hit **Parse URL** — show auto-fill of title and detected entities.
4. Submit — describe the pipeline running:
   > "Scout (Gemini Flash) → Extractor (Gemini 1.5 Pro) → Resolver → Critic → Scorer"
5. Show the new claim appearing with a model attribution badge:
   > "extracted by gemini-2.5-flash" — every claim tracks which model produced it.

**Talk track**: "The pipeline is a LangGraph state machine. Each node in the graph is
a separate agent with a specific job. The resolver canonicalizes entity names against
a 200-entity registry. The critic does adversarial scoring — it rejects about 30% of
raw claims as insufficiently supported."

---

## 4:30 — The Graph (3 minutes)

1. Navigate to `/graph`. Show ~200 nodes, color-coded by entity type.
2. Click **Show Legend** (top-right overlay) — walk through the color coding.
3. Click regime filter: **GRID_BOTTLENECK**. Graph re-fetches with filtered edges.
4. Click a specific node (e.g., **GE Vernova**). The right-side panel slides in:
   - Entity name, type, bottleneck score bar
   - "Open Full Detail" link
5. Point to a gold-bordered node: "That's a watched entity — added to the watchlist
   for live score monitoring."
6. Point to a pulsing node: "Top 5 bottleneck nodes pulse — these are the entities
   where claim density and confidence are highest."
7. Hit **Export PNG** — show download trigger.

---

## 7:30 — Thesis Run + Scenario Branch (5 minutes)

1. Navigate to `/thesis`.
2. Type: **"Power constraint moat benefits nuclear and gas peakers"**
3. Hit **Run** — show progress indicator, then results:
   - Support score: ~37.5%
   - Contradiction score: ~12.1%
   - Top 5 bottleneck nodes in the transmission chain
4. Click **"FERC fast-track interconnection approved"** scenario button.
5. Show side-by-side: support drops to ~21%, contradiction rises.
6. Read the delta narrative aloud.

**Talk track**: "This is the key insight — the analyst can stress-test a thesis against
a hypothetical regime change without mutating the main graph. The scenario branches
hold a parallel edge set and recompute scores against the same claims. That's the
'what-if' workspace."

**Technical note for interviewers**: "The scorer has 5 components: evidence intensity,
recency, cross-source agreement, market confirmation, and house view weight. Each is
configurable, and the weights are exposed in the API for model transparency."

---

## 12:30 — Streaming Memo (2 minutes)

1. Navigate to `/memo`.
2. Toggle **Stream ON**.
3. Hit **Generate Memo** — show text appearing word by word (SSE stream).
4. When complete, hit **Download PDF**.

**Talk track**: "Memo generation uses Gemini 1.5 Pro with a style-specific prompt —
buyside LP, sellside note, or internal brief. The streaming uses Server-Sent Events
so the analyst sees text as it generates, not after a 20-second wait."

---

## 14:30 — House View + Weekly Digest (2 minutes)

1. Navigate to `/house-view`.
2. Set **conviction = HIGH** on **Constellation Energy Group**.
3. Confirm the narrative regenerates on the dashboard.
4. Navigate to `/digest`. Hit **Generate** — show weekly summary output.

**Talk track**: "The house view is the analyst's conviction layer on top of the
evidence graph. High conviction adds +10 pts to the bottleneck score; low subtracts.
The weekly digest generator summarizes all new claims from the past 7 days into a
briefing — designed to go out every Monday morning."

---

## 16:30 — Technical Q&A Setup (90 seconds)

Open `docs/ARCHITECTURE_DEEP_DIVE.md` in a second tab.

> "Happy to go deeper on any of these:
> - Scorer design and 5-component weighting
> - BigQuery schema vs SQLite dual-mode routing
> - Why LangGraph over vanilla async functions (state machine advantages)
> - Multi-model routing rationale (Gemini for speed, Gemini Pro for reasoning)
> - What v2 would look like — real-time market signal feeds, portfolio integration"

---

## Common interview questions — prep answers

**Q: How does the graph handle conflicting claims?**
A: The critic agent flags contradictions by comparing new claims against the existing
claim set for the same entity pair. Contradicted claims get `status=flagged` with
a reduced confidence score. The thesis runner reports both support and contradiction
scores separately.

**Q: Why not just use an LLM to answer the thesis directly?**
A: The graph structure lets us trace *which specific claims* support or contradict
a thesis, with their evidence sources. Pure LLM answers are opaque — you can't
audit why it said what it said. Every score here is explainable back to a claim,
which is traceable to a document.

**Q: What's the biggest limitation?**
A: The evidence corpus is limited by what's been ingested. With a Bloomberg terminal
feed or RSS pipeline, coverage would be dramatically better. Right now it requires
manual URL submission.
