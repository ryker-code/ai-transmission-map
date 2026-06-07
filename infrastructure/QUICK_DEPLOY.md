# Quick Deploy — 3-Command Railway + Vercel

Run these from your **local machine** (not Codespace) where browser auth works.

## Backend → Railway (~3 minutes)

```bash
npm install -g @railway/cli
railway login
cd /path/to/ai-transmission-map
railway init --name aitm-backend
railway up
railway domain     # Copy the https URL (e.g. aitm-backend.up.railway.app)
```

Set environment variables in the Railway dashboard:
```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
AITM_API_KEY=<choose-a-secret-key>
```

## Frontend → Vercel (~2 minutes)

```bash
npm install -g vercel
cd frontend
NEXT_PUBLIC_API_URL=https://aitm-backend.up.railway.app  # from Railway step
NEXT_PUBLIC_API_KEY=<same-secret-key-as-AITM_API_KEY>
npx vercel --prod \
  --env NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
  --env NEXT_PUBLIC_API_KEY=$NEXT_PUBLIC_API_KEY
```

## Smoke Test

Once both are deployed:
```bash
curl https://aitm-backend.up.railway.app/health | python3 -m json.tool
# Expected: {"status": "ok", "version": "1.0.0", "db": "sqlite", "entity_count": 200, "claim_count": 80}

curl https://aitm-backend.up.railway.app/health/db | python3 -m json.tool
# Expected: {"db_active": "sqlite", "bq_available": false, "entity_count": 200, ...}
```

## Estimated Monthly Cost

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Railway | $5/mo after trial | Always-on backend |
| Vercel | Free | Static + serverless frontend |
| Railway + BigQuery | +$0 | BigQuery free tier covers demo usage |

## Already Configured

- `railway.json` — NIXPACKS build, uvicorn start command
- `frontend/next.config.ts` — standalone output for Vercel
- `infrastructure/cloud_run/` — Dockerfile + cloudbuild.yaml for GCP
- `infrastructure/DEPLOYMENT_GUIDE.md` — full step-by-step guide

## One-Click Codespaces (No Deploy Required)

Anyone can run a full dev environment in 60 seconds:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ryker-code/ai-transmission-map)

This starts both backend and frontend automatically with 200 entities and 80 claims pre-seeded.
