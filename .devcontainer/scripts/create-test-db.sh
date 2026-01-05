#!/bin/bash -e
# Creates and initializes a NAV database for integration tests in the devcontainer.
# This script is designed to work with an external PostgreSQL container,
# unlike the tests/docker/scripts/create-db.sh which manages PostgreSQL clusters directly.
#
# IMPORTANT: This uses a separate 'nav_test' database to avoid destroying the dev database.
# The test config directory (NAV_CONFIG_DIR) is set up by tests/conftest.py before this runs.

set -o pipefail

# Configuration - use a separate test database!
: "${PGHOST:=db}"
: "${PGPORT:=5432}"
: "${PGUSER:=nav}"
: "${PGPASSWORD:=nav}"
: "${PGDATABASE:=nav_test}"
: "${ADMINPASSWORD:=admin}"

# Find test data SQL
WORKSPACE_DIR="${WORKSPACE:-/workspaces/nav}"
TEST_DATA_SQL="${WORKSPACE_DIR}/tests/docker/scripts/test-data.sql"

echo "=== Integration Test Database Setup ==="
echo "Database: ${PGDATABASE} on ${PGHOST}:${PGPORT}"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" > /dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: PostgreSQL is not ready after 30 seconds"
        exit 1
    fi
    sleep 1
done

# Fix collation version mismatch if present (needed for createdb to work)
echo "Checking and fixing collation versions..."
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c "ALTER DATABASE template1 REFRESH COLLATION VERSION;" 2>/dev/null || true
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;" 2>/dev/null || true

# Create database schema (drops existing if present)
echo "Creating database schema with navsyncdb..."
navsyncdb -c --drop-database

# Set admin password
if [ -n "$ADMINPASSWORD" ]; then
    echo "Setting admin password..."
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c \
        "UPDATE account SET password = '${ADMINPASSWORD}' WHERE login = 'admin'"
fi

# Load test data
if [ -f "$TEST_DATA_SQL" ]; then
    echo "Loading test data from ${TEST_DATA_SQL}..."
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$TEST_DATA_SQL"
else
    echo "WARNING: Test data file not found at ${TEST_DATA_SQL}"
fi

echo "=== Database setup complete ==="
