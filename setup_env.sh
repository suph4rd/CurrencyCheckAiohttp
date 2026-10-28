#!/usr/bin/env bash

set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ -e docker_settings.env || -L docker_settings.env ]]; then
    echo "Keeping existing docker_settings.env."
    exit 0
fi

password=$(openssl rand -hex 24)

# Restrict access and refuse to overwrite a file created by another process.
(
    umask 077
    set -o noclobber
    cat > docker_settings.env <<EOF
APP_HOST=0.0.0.0
APP_PORT=7777
DATABASE_URI=postgresql+asyncpg://currencycheck:${password}@db:5432/currency_db
DATABASE_URI_MIGRATION=postgresql+psycopg2://currencycheck:${password}@db:5432/currency_db
POSTGRES_DB=currency_db
POSTGRES_USER=currencycheck
POSTGRES_PASSWORD=${password}
EOF
)

echo "Created docker_settings.env with a random PostgreSQL password."
