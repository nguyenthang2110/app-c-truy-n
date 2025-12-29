#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create venv if missing
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
  echo "[+] Creating virtualenv at .venv"
  python3 -m venv "$SCRIPT_DIR/.venv"
fi

# Activate venv
source "$SCRIPT_DIR/.venv/bin/activate"

# Upgrade pip & install deps
python -m pip install --upgrade pip wheel
pip install -r "$SCRIPT_DIR/requirements.txt"

# Run Streamlit
export PYTHONIOENCODING=utf-8
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

PORT="${PORT:-8502}"
echo "[+] Starting app on http://localhost:${PORT}"
exec streamlit run "$SCRIPT_DIR/app.py" --server.port "$PORT" --server.headless true