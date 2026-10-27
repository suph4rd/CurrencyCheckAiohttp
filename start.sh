#!/usr/bin/env bash

set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    python_bin="$VIRTUAL_ENV/bin/python"
elif [[ -x .venv/bin/python ]]; then
    python_bin="$PWD/.venv/bin/python"
elif [[ -x venv/bin/python ]]; then
    python_bin="$PWD/venv/bin/python"
else
    python_bin=python3
fi

if ! "$python_bin" -c 'import gunicorn' 2>/dev/null; then
    echo "Gunicorn is missing. Install requirements.txt in your Python environment." >&2
    exit 1
fi

# Report configuration/import errors once, before spawning workers.
"$python_bin" -c 'import app.server'

exec "$python_bin" -m gunicorn app.server:current_app \
    --bind localhost:8000 \
    --worker-class aiohttp.GunicornWebWorker \
    --workers 4
