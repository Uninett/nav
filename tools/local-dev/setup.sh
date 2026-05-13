#!/bin/bash
set -euo pipefail

# One-time setup for local NAV development (without devcontainers).
#
# Prerequisites:
#   - uv, Node.js/npm, Docker, pg_dump (>= 17)
#   - System libraries: libpq, net-snmp, libjpeg
#
# Usage:
#   make local-setup

cd "$(cd "$(dirname "$0")/../.." && pwd)"

NAV_PG_PORT="${NAV_PG_PORT:-5434}"
export NAV_PG_PORT

info()  { echo -e "\033[0;32m==>\033[0m $*"; }
error() { echo -e "\033[0;31m==> ERROR:\033[0m $*" >&2; }

# --- Check prerequisites ---
info "Checking prerequisites..."
MISSING=0
for cmd in uv node npm docker; do
    command -v "$cmd" &>/dev/null || { error "$cmd is not installed."; MISSING=1; }
done
[ "$MISSING" -eq 1 ] && exit 1

# --- Install dependencies ---
info "Installing Python dependencies..."
uv sync --python "${NAV_PYTHON:-3.11}" --all-extras --all-groups

info "Installing npm dependencies and building CSS..."
npm install
npm run build:sass

# --- Configure virtualenv for local development ---
uv run python tools/local-dev/configure.py

# --- Start infrastructure and sync database ---
info "Starting PostgreSQL and Graphite containers..."
docker compose -f tools/local-dev/docker-compose.yml up -d

info "Waiting for PostgreSQL..."
for _ in $(seq 1 30); do
    PGPASSWORD=nav psql -h 127.0.0.1 -p "$NAV_PG_PORT" -U nav -d nav -c "SELECT 1" &>/dev/null && break
    sleep 1
done
if ! PGPASSWORD=nav psql -h 127.0.0.1 -p "$NAV_PG_PORT" -U nav -d nav -c "SELECT 1" &>/dev/null; then
    error "PostgreSQL did not become ready in time."
    exit 1
fi

info "Syncing NAV database schema..."
uv run navsyncdb

echo ""
info "Local development environment is ready!"
cat <<EOF

  Start the web server:
    uv run django-admin runserver

  Watch SASS for changes (optional):
    make sasswatch

  Infrastructure services:
    make local-up       # start
    make local-down     # stop

  Run tests:
    uv run pytest tests/unittests/

EOF
