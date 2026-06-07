# CLAUDE.md — AI Transmission Map

## Project Identity
You are building "AI Infrastructure Transmission Map" — an investor thesis tool
that maps how AI demand propagates through semiconductors, data centers,
transformers, utilities, grid infrastructure, and public markets.
US-scope only. Primary user: equity investor running thesis interrogation.

## Stack (NEVER deviate)
- Frontend: Next.js 15, TypeScript strict, Tailwind CSS, shadcn/ui, react-force-graph-2d
- Backend: FastAPI, Python 3.11, LangGraph 0.1.x, Pydantic v2
- Database: Google BigQuery via google-cloud-bigquery SDK (SQLite stub if no GCP creds)
- Agent models: Claude claude-opus-4-5 (complex reasoning), Gemini 2.0 Flash (fast extraction)
- Deploy: Vercel (frontend), Cloud Run (backend)

## Coding Rules
- ALWAYS write Pydantic models for every API request and response
- ALWAYS add error handling and logging to every route
- NEVER hardcode API keys — always load from environment via config.py
- ALWAYS add a docstring to every agent function
- NEVER skip writing the TypeScript type in frontend/lib/types.ts when adding a new schema
- Prefer async/await throughout FastAPI
- All Python files must pass: python -m py_compile <file>

## File Creation Order (for every new feature)
1. Pydantic schema in backend/api/schemas.py
2. BigQuery migration in db/migrations/
3. FastAPI route in api/routes/
4. LangGraph agent function in agents/
5. TypeScript type in frontend/lib/types.ts
6. React component in frontend/components/
7. Test in backend/tests/

## Autonomous Run Rules
- Ambiguous task → pick conservative interpretation + add TODO
- Failed command → retry once, then log to docs/known_issues.md and continue
- Missing API key → use placeholder, add key name to .env.example
- Never delete working code without creating a backup branch
- After each phase, commit to git with a descriptive message
- Never stop before 6:00 AM EDT unless all phases are complete
