#!/usr/bin/env bash
# Start the AI Translation Service using the project's own virtualenv.
#
# Launching through .venv/bin/python is what avoids the classic
#   ModuleNotFoundError: No module named 'torch'
# which happens when the app is started with a system python/uvicorn that
# doesn't have the ML packages installed.

set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"

# 1. Is the virtualenv there?
if [ ! -x "$PY" ]; then
  echo "✗ No virtualenv found at .venv"
  echo "  Create it (Apple Silicon, Python 3.12) and install deps:"
  echo "    uv venv .venv --python 3.12"
  echo "    uv pip install -p .venv/bin/python -r requirements.txt -r requirements-ml.txt"
  exit 1
fi

# 2. Are the ML packages installed? (this is the cause of the torch error)
if ! "$PY" -c "import torch, transformers, faster_whisper" 2>/dev/null; then
  echo "✗ ML dependencies are missing from .venv"
  echo "  (this is what causes: ModuleNotFoundError: No module named 'torch')"
  echo "  Install them:"
  echo "    uv pip install -p .venv/bin/python -r requirements-ml.txt"
  exit 1
fi

# 3. Optional overrides from .env (e.g. HF_TOKEN, DEVICE, PORT)
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
PORT="${PORT:-8000}"

# 4. Open the browser once the server is up
( sleep 3; open "http://localhost:${PORT}" >/dev/null 2>&1 || true ) &

echo "→ AI Translation Service: http://localhost:${PORT}   (Ctrl+C to stop)"
exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" "$@"
