#!/bin/bash
# Start TrendSee in development mode (no Docker needed)
# Prerequisites: Python 3.12+, Node 20+, Redis running locally

set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)

echo "🚀 Starting TrendSee Dev Environment"

# Copy env if not exists
[ ! -f "$ROOT/.env" ] && cp "$ROOT/.env.example" "$ROOT/.env" && echo "📋 Created .env from .env.example — please add your API keys"

# Backend
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  echo "🐍 Creating Python venv..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
playwright install chromium --with-deps 2>/dev/null || true

echo "▶️  Starting FastAPI (port 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo "▶️  Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=warning --concurrency=1 &
WORKER_PID=$!

echo "▶️  Starting Celery Beat..."
celery -A app.tasks.celery_app beat --loglevel=warning &
BEAT_PID=$!

# Frontend
cd "$ROOT/frontend"
npm install -q
echo "▶️  Starting Vite dev server (port 5173)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ All services started!"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."

trap "kill $API_PID $WORKER_PID $BEAT_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" INT TERM
wait
