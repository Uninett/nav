#!/bin/bash -e
# This simple script is designed to run inside a docker development instance,
# doing a full database drop-and-restore cycle
#
# Usage example (from host system):
# ssh <production-nav> /usr/lib/nav/navpgdump --only-open-arp --only-open-cam | \
#   docker exec -i <container-id> full-nav-restore.sh
#
if ! which navsyncdb 2>/dev/null; then
    echo "NAV source directory not correctly mounted on /source" > /dev/stderr
    exit 1
fi
sudo nav stop
export PGHOST=postgres
export PGUSER=postgres

echo "Forcefully terminating all other connections to the database:"
psql -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'nav'
  AND pid <> pg_backend_pid();
"

navsyncdb --drop-database --create --restore -
echo "NOT starting NAV after db restore, please do it manually!"

# If Django runserver is running, this ensures it reloads after the database is
# replaced:
test -f /source/python/nav/__init__.py && touch /source/python/nav/__init__.py
