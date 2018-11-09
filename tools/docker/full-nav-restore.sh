#!/bin/bash -e
# This simple script is designed to run inside a docker development instance,
# doing a full database drop-and-restore cycle
#
# Usage example (from host system):
# ssh <production-nav> /usr/lib/nav/navpgdump --only-open-arp --only-open-cam | \
#   docker exec -i <container-id> full-nav-restore.sh
#
if [ ! -x /source/bin/navsyncdb ]; then
    echo "NAV source directory not correctly mounted on /source" > /dev/stderr
    exit 1
fi
nav stop
supervisorctl stop web
export PGHOST=postgres
export PGUSER=postgres
/source/bin/navsyncdb --drop-database --create --restore -
supervisorctl start web
echo "NOT starting NAV after db restore, please do it manually!"
