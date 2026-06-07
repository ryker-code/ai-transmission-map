# ANTIGRAVITY.md — AI Transmission Map

## Model Selection
- Gemini 3.1 Pro: multi-file refactors, orchestrator logic, DB migrations
- Gemini 3.5 Flash: single-file scripts, terminal debugging, CSS fixes

## Always-on context (always @mention these)
- @backend/api/schemas.py — source of truth for all data shapes
- @backend/db/migrations/ — check before creating any new table
- @CLAUDE.md — global rules always apply

## Permission Mode
- Auto-approve: file creation, pip install, npm install, pytest, git commit
- Request Review: any DROP TABLE, DELETE FROM, git push to main
- NEVER auto-approve writes to .env (only .env.example)
