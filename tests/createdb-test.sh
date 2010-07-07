#!/bin/sh -e
#
# This script is instended to simply test creating a nav database
# If the word ERROR is found in the createdb output we assume it failed.
# (This due to the rather poor return values from psql)

if [ -z $PGDATABASE ]; then echo PGDATABASE not set; exit 1; fi
if [ -z $PGUSER ]; then echo PGUSER not set; exit 1; fi

# Cleanup any existing DB
dropdb $PGDATABASE || true

cd doc/sql

# Try creating DB
../../tools/retval-wrapper.sh ./createdb.sh -d $PGDATABASE -u $PGUSER -U
