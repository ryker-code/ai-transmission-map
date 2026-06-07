# Known Issues

## Day 1

### 1. langchain version conflict
**Symptom:** `pip install -r requirements.txt` fails with ResolutionImpossible.  
**Fix:** Relaxed to range constraints (`>=x,<y`) for langchain-core, langchain-anthropic, langchain-google-genai, langgraph.  
**Status:** Resolved.

### 2. Seed loader must be invoked as module
**Symptom:** `python backend/db/seed_loader.py` raises `ModuleNotFoundError: No module named 'backend'`.  
**Fix:** Use `python -m backend.db.seed_loader` from repo root. Makefile `seed` target updated accordingly.  
**Status:** Resolved.

### 3. Deprecation warnings (non-blocking)
- `datetime.utcnow()` deprecated in Python 3.12 — use `datetime.now(datetime.UTC)` in Day 2 refactor.
- FastAPI `@app.on_event("startup")` deprecated — migrate to `lifespan` handler in Day 2.
- Pydantic `model_used` field name conflicts with `model_` namespace — add `model_config['protected_namespaces'] = ()` to MemoResponse in Day 2.  
**Status:** Deferred to Day 2.
