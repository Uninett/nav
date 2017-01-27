#!/bin/bash -e
cd /source
export PGHOST=postgres PGUSER=postgres
psql -l | grep -q nav || sql/syncdb.py -c
sudo -u nav /source/sql/syncdb.py -o
