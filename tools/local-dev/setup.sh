#!/bin/bash
set -euo pipefail

# One-time setup for local NAV development (without devcontainers).
#
# Prerequisites:
#   - Python 3.9+ and uv (https://docs.astral.sh/uv/)
#   - Node.js and npm
#   - Docker (for PostgreSQL and Graphite)
#   - System libraries: libpq, net-snmp, libjpeg, zlib
#     Optional: libldap + libsasl2 (for LDAP authentication)
#
# Usage:
#   make local-setup

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}==>${NC} $*"; }
warn()  { echo -e "${YELLOW}==> WARNING:${NC} $*"; }
error() { echo -e "${RED}==> ERROR:${NC} $*" >&2; }

# --- Check basic prerequisites ---
check_command() {
    if ! command -v "$1" &>/dev/null; then
        error "$1 is not installed. $2"
        return 1
    fi
}

info "Checking prerequisites..."
MISSING=0
check_command uv "Install from https://docs.astral.sh/uv/" || MISSING=1
check_command node "Install Node.js from your package manager or https://nodejs.org/" || MISSING=1
check_command npm "Comes with Node.js" || MISSING=1
check_command docker "Install from https://docs.docker.com/get-docker/" || MISSING=1

# pg_dump must match or exceed the Docker PostgreSQL version (17)
if command -v pg_dump &>/dev/null; then
    PG_DUMP_VERSION=$(pg_dump --version | grep -oE '[0-9]+' | head -1)
    if [ "$PG_DUMP_VERSION" -lt 17 ] 2>/dev/null; then
        warn "pg_dump is version $PG_DUMP_VERSION, but PostgreSQL 17 is used."
        echo "    macOS:  brew install postgresql@17"
        MISSING=1
    fi
else
    warn "pg_dump is not installed."
    echo "    macOS:  brew install postgresql@17"
    MISSING=1
fi

if [ "$MISSING" -eq 1 ]; then
    error "Please install the missing prerequisites and re-run this script."
    exit 1
fi

# --- Check system libraries ---
info "Checking system libraries..."
LIBS_MISSING=0

find_header() {
    local header="$1"

    # Standard system paths
    for dir in /usr/include /usr/local/include; do
        [ -f "$dir/$header" ] && return 0
    done

    # Homebrew (macOS) — check both Apple Silicon and Intel prefixes
    for prefix in /opt/homebrew /usr/local; do
        if [ -d "$prefix/include" ]; then
            find -L "$prefix/include" -path "*/$header" -print -quit 2>/dev/null | grep -q . && return 0
        fi
        if [ -d "$prefix/opt" ]; then
            find -L "$prefix/opt" -path "*/include*/$header" -print -quit 2>/dev/null | grep -q . && return 0
        fi
    done

    return 1
}

check_lib() {
    local name="$1"
    local pkg_config_name="$2"
    local header="$3"
    local install_hint="$4"

    # Try pkg-config first
    if pkg-config --exists "$pkg_config_name" 2>/dev/null; then
        return 0
    fi

    # Search common header paths (handles Homebrew, Nix, standard locations)
    if find_header "$header"; then
        return 0
    fi

    warn "$name not found. Install it:"
    echo "    $install_hint"
    LIBS_MISSING=1
}

check_lib "PostgreSQL client library (libpq)" "libpq" "libpq-fe.h" \
    "Debian/Ubuntu: sudo apt install libpq-dev
    Fedora/RHEL:   sudo dnf install libpq-devel
    Arch:          sudo pacman -S postgresql-libs
    macOS:         brew install libpq
    Nix:           nix-shell -p postgresql"

check_lib "Net-SNMP library" "netsnmp" "net-snmp/net-snmp-config.h" \
    "Debian/Ubuntu: sudo apt install libsnmp-dev
    Fedora/RHEL:   sudo dnf install net-snmp-devel
    Arch:          sudo pacman -S net-snmp
    macOS:         brew install net-snmp
    Nix:           nix-shell -p net-snmp"

check_lib "libjpeg (for Pillow)" "libjpeg" "jpeglib.h" \
    "Debian/Ubuntu: sudo apt install libjpeg-dev
    Fedora/RHEL:   sudo dnf install libjpeg-turbo-devel
    Arch:          sudo pacman -S libjpeg-turbo
    macOS:         brew install jpeg
    Nix:           nix-shell -p libjpeg"

if [ "$LIBS_MISSING" -eq 1 ]; then
    warn "Some system libraries appear to be missing."
    echo "    Python package installation may fail without them."
    echo ""
    read -r -p "Continue anyway? [y/N] " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# --- Install Python dependencies ---
info "Installing Python dependencies (Python 3.11)..."
uv sync --python 3.11 --all-extras --all-groups

# --- Get the virtualenv path ---
read -r VENV_DIR SITE_PACKAGES <<< "$(uv run python -c "import sys, site; print(sys.prefix, site.getsitepackages()[0])")"
NAV_CONFIG_DIR="$VENV_DIR/etc/nav"

info "Virtualenv: $VENV_DIR"
info "NAV config: $NAV_CONFIG_DIR"

# --- Configure virtualenv defaults ---
# sitecustomize.py runs on every Python startup from this venv.
# setdefault ensures explicit exports still take precedence.
# The macOS libcrypto patch must live here (not just in nav.Snmp) because
# multiple modules import pynetsnmp independently.
info "Configuring virtualenv defaults..."
cat > "$SITE_PACKAGES/sitecustomize.py" <<'PYEOF'
import os
import sys

for key, value in {
    "DJANGO_SETTINGS_MODULE": "nav.django.settings",
    "PGHOST": "127.0.0.1",
    "PGPORT": "5433",
    "PGUSER": "nav",
    "PGPASSWORD": "nav",
}.items():
    os.environ.setdefault(key, value)

if sys.platform == "darwin":
    import ctypes
    import ctypes.util
    from pathlib import Path

    _real_init = ctypes.CDLL.__init__

    class _PatchedCDLL(ctypes.CDLL):
        def __init__(self, name, *args, **kwargs):
            if name and str(name).endswith("libcrypto.dylib"):
                return _real_init(self, None, *args, **kwargs)
            return _real_init(self, name, *args, **kwargs)

    ctypes.CDLL = _PatchedCDLL

    # macOS ships a 2006-era libtidy; prefer Homebrew's modern version
    # so that pytidylib (used by integration tests) gets consistent results.
    _find_library = ctypes.util.find_library
    def _patched_find_library(name):
        if name == "tidy":
            for prefix in ("/opt/homebrew", "/usr/local"):
                _tidy = Path(prefix) / "opt/tidy-html5/lib/libtidy.dylib"
                if _tidy.exists():
                    return str(_tidy)
        return _find_library(name)
    ctypes.util.find_library = _patched_find_library
PYEOF

# --- Install NAV config files ---
info "Installing NAV configuration files..."
uv run nav config install "$NAV_CONFIG_DIR" 2>/dev/null

# --- Configure db.conf for local Docker PostgreSQL ---
DB_CONF="$NAV_CONFIG_DIR/db.conf"
info "Configuring $DB_CONF..."
cat > "$DB_CONF" <<EOF
dbhost=127.0.0.1
dbport=5433
db_nav=nav
script_default=nav
userpw_nav=nav
EOF

# --- Configure nav.conf for local development ---
NAV_CONF="$NAV_CONFIG_DIR/nav.conf"
UPLOAD_DIR="$VENV_DIR/var/nav/uploads"
mkdir -p "$UPLOAD_DIR"

info "Configuring $NAV_CONF..."
sed -i.bak \
    -e "s/^NAV_USER=.*/NAV_USER=$(whoami)/" \
    -e 's/^#DJANGO_DEBUG=True/DJANGO_DEBUG=True/' \
    -e "s,^#UPLOAD_DIR=.*,UPLOAD_DIR=$UPLOAD_DIR," \
    "$NAV_CONF"
rm -f "$NAV_CONF.bak"
# Append settings that weren't present as comments in the template
grep -q '^DJANGO_DEBUG=True' "$NAV_CONF" || echo "DJANGO_DEBUG=True" >> "$NAV_CONF"
grep -q '^UPLOAD_DIR=' "$NAV_CONF" || echo "UPLOAD_DIR=$UPLOAD_DIR" >> "$NAV_CONF"

# --- Configure graphite.conf for local Docker Graphite ---
GRAPHITE_CONF="$NAV_CONFIG_DIR/graphite.conf"
info "Configuring $GRAPHITE_CONF..."
cat > "$GRAPHITE_CONF" <<EOF
[carbon]
host=localhost
port=2003

[graphiteweb]
base=http://localhost:8088/
EOF

# --- Install frontend dependencies ---
info "Installing npm dependencies..."
npm install

# --- Build CSS ---
info "Building SASS/CSS..."
npm run build:sass

# --- Start infrastructure services ---
info "Starting PostgreSQL and Graphite containers..."
docker compose -f docker-compose.local.yml up -d

# --- Wait for PostgreSQL to be ready ---
pg_ready() { PGPASSWORD=nav psql -h 127.0.0.1 -p 5433 -U nav -d nav -c "SELECT 1" &>/dev/null; }

info "Waiting for PostgreSQL to accept connections..."
for _ in $(seq 1 30); do
    pg_ready && break
    sleep 1
done

if ! pg_ready; then
    error "PostgreSQL did not become ready in time."
    exit 1
fi

# --- Sync database ---
# navsyncdb needs superuser access for hstore extension creation.
# In our Docker setup, the "nav" user IS the superuser, so we pass
# these env vars so navsyncdb uses "nav" for both regular and superuser ops.
info "Syncing NAV database schema..."
PGHOST=127.0.0.1 PGPORT=5433 PGUSER=nav PGPASSWORD=nav uv run navsyncdb

# --- Install pre-commit hooks ---
info "Installing pre-commit hooks..."
uv run pre-commit install

# --- Done ---
echo ""
info "Local development environment is ready!"
echo ""
echo "  Start the web server:"
echo "    uv run django-admin runserver"
echo ""
echo "  Watch SASS for changes (optional):"
echo "    make sasswatch"
echo ""
echo "  Infrastructure services:"
echo "    make local-up       # start"
echo "    make local-down     # stop"
echo ""
echo "  Run tests:"
echo "    uv run pytest tests/unittests/"
echo ""
