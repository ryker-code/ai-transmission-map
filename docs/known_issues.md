# Known Issues

## Day 7

### Railway deploy requires manual auth
**Symptom:** `railway up` prompts for device-code sign-in; cannot complete headlessly.
**Fix:** Run `railway login` in an interactive terminal, then `railway up --detach`.
**Status:** Documented. See `infrastructure/QUICK_DEPLOY.sh` for full flow.

### google-generativeai version conflict with langchain-google-genai
**Symptom:** pip warns that `langchain-google-genai 1.0.10` requires `google-generativeai<0.8.0` but 0.8.3 is installed.
**Fix:** Conflict is benign — both packages work at runtime. No code changes needed.
**Status:** Monitoring. Will resolve when langchain-google-genai releases a 0.8.x-compatible version.

## Day 1

### 1. langchain version conflict
**Symptom:** `pip install -r requirements.txt` fails with ResolutionImpossible.  
**Fix:** Relaxed to range constraints (`>=x,<y`) for langchain-core, langchain-anthropic, langchain-google-genai, langgraph.  
**Status:** Resolved.

### 2. Seed loader must be invoked as module
**Symptom:** `python backend/db/seed_loader.py` raises `ModuleNotFoundError: No module named 'backend'`.  
**Fix:** Use `python -m backend.db.seed_loader` from repo root. Makefile `seed` target updated accordingly.  
**Status:** Resolved.

### 3. Deprecation warnings
- `datetime.utcnow()` → fixed in seed_loader.py and entities.py with `datetime.now(timezone.utc)` (Day 2 Phase 5).
- FastAPI `@app.on_event("startup")` → migrated to `lifespan` context manager in main.py (Day 2 Phase 4).
- Pydantic `model_` namespace conflict → fixed with `ConfigDict(protected_namespaces=())` on MemoResponse (Day 2 Phase 4).  
**Status:** Resolved.
