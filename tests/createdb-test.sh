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

# Create file to store output
out=`mktemp`

# Try creating DB
./createdb.sh -d $PGDATABASE -u $PGUSER -U 2>&1 | tee $out

# Check result and return status
retval=`grep ERROR $out | wc -l`
rm $out
exit $retval

