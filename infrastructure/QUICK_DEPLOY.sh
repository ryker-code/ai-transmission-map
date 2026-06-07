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
