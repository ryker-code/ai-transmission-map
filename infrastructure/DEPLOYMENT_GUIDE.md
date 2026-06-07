# Deployment Guide — AI Transmission Map

## Option A: Vercel (Frontend, ~2 minutes)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `ryker-code/ai-transmission-map`
3. Set **Root Directory**: `frontend`
4. Add env var:
   ```
   NEXT_PUBLIC_API_URL=<your backend URL>
   ```
5. Click **Deploy**

Vercel auto-detects Next.js and uses standalone output (`next.config.ts`).

---

## Option B: Railway (Backend, ~5 minutes)

1. Go to [railway.app/new](https://railway.app/new)
2. **Deploy from GitHub**: `ryker-code/ai-transmission-map`
3. Set root directory: `backend`
4. Add env vars from `.env.example`
5. Set start command:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

Railway auto-installs `requirements.txt` and exposes a public URL.

---

## Option C: Render (Free tier, Backend)

1. Go to [render.com/deploy](https://render.com/deploy)
2. **New Web Service** → Connect GitHub
3. Repository: `ryker-code/ai-transmission-map`
4. Root directory: `backend`
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add env vars from `.env.example`

Render free tier spins down after 15 minutes of inactivity — use Railway for always-on.

---

## Option D: Cloud Run (Backend, Production-grade)

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
cd backend
gcloud run deploy ai-transmission-map-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ANTHROPIC_API_KEY=...,GOOGLE_API_KEY=..."
```

`Dockerfile` and `cloudbuild.yaml` are already configured in `/infrastructure/cloud_run/`.

---

## One-Click Codespaces Demo

Anyone can launch a fully working dev environment in 60 seconds:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ryker-code/ai-transmission-map)

The Codespace auto-starts the backend (`uvicorn`) and frontend (`npm run dev`) via `.devcontainer/` configuration.

---

## Quick Start (Local)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

Copy `.env.example` → `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes (for LLM features) | Claude claude-opus-4-5 API key |
| `GOOGLE_API_KEY` | Yes (for Gemini Scout) | Google AI Studio key |
| `OPENAI_API_KEY` | Optional | For Whisper voice transcription |
| `GOOGLE_CLOUD_PROJECT` | Optional | BigQuery project (SQLite fallback if absent) |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend URL (default: http://localhost:8000) |
