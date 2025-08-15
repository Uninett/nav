#!/bin/bash -e
# This simple script is designed to run inside a devcontainer doing a full
# database drop-and-restore cycle.  It expects the SQL schema to load to
# be its input on stdin.
#
if ! which navsyncdb 2>/dev/null; then
    echo "navsyncdb not available on PATH" > /dev/stderr
    exit 1
fi
echo "Stopping NAV background daemons:"
sudo nav stop

echo "Forcefully terminating all other connections to the database:"
psql -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'nav'
  AND pid <> pg_backend_pid();
"

echo "Resetting database, expecting dump on stdin..."
navsyncdb --drop-database --create --restore -
echo "================================================================"
echo "Restore complete. Please start NAV processes manually as needed."
