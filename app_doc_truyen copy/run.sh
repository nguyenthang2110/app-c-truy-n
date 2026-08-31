#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create venv if missing
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
  echo "[+] Creating virtualenv at .venv"
  python3 -m venv "$SCRIPT_DIR/.venv"
  VENV_CREATED=true
else
  VENV_CREATED=false
fi

# Activate venv
source "$SCRIPT_DIR/.venv/bin/activate"

# Upgrade the packaging tools only for a new environment. Reinstalling pip on
# every launch made restarts unnecessarily slow.
if [ "$VENV_CREATED" = true ]; then
  python -m pip install --upgrade pip wheel
fi

REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
REQUIREMENTS_STAMP="$SCRIPT_DIR/.venv/.requirements.sha256"
REQUIREMENTS_HASH="$(python -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$REQUIREMENTS_FILE")"
INSTALLED_HASH="$(sed -n '1p' "$REQUIREMENTS_STAMP" 2>/dev/null || true)"

if [ "$REQUIREMENTS_HASH" != "$INSTALLED_HASH" ] || \
   ! python -c 'import bs4, lxml, readability, requests, streamlit' 2>/dev/null; then
  python -m pip install --disable-pip-version-check -r "$REQUIREMENTS_FILE"
  printf '%s\n' "$REQUIREMENTS_HASH" > "$REQUIREMENTS_STAMP"
fi

# Run Streamlit
export PYTHONIOENCODING=utf-8
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

PORT="${PORT:-8502}"
BIND_ADDRESS="${BIND_ADDRESS:-127.0.0.1}"
echo "[+] Starting app on http://${BIND_ADDRESS}:${PORT}"
exec streamlit run "$SCRIPT_DIR/app.py" \
  --server.address "$BIND_ADDRESS" \
  --server.port "$PORT" \
  --server.headless true
