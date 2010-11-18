#!/bin/sh
#
# Helper script to allow simpler setup of required enviroment for performing
# NAV tests.
#
# Use of virtualenv should probably be deprecated in favor of a newer nose
# version installed through backports.

set -e

test -z "$PGDATABASE" && echo PGDATABASE missing && exit 1
test -z "$PGUSER"     && echo PGUSER missing     && exit 1
test -z "$1"          && echo dir missing        && exit 1

BUILDDIR="$1/build"
VIRTENV="$1/.env"

# Clear build directory
test -d "$BUILDDIR" && rm -rf "$BUILDDIR"

# Create virtualenv for some required python packages, and keep it around to
# avoid hitting the network each time a job runs.
if [ -d "$VIRTENV" ]; then
    echo "**> virtualenv exists"
else
    echo "**> creating virtualenv"
    virtualenv "$VIRTENV"
    source "$VIRTENV/bin/activate"
    easy_install nose
fi

# Cleanup any existing DB
dropdb $PGDATABASE || true

(cd sql; ./createdb.sh -d $PGDATABASE -u $PGUSER -U)

# Make install code into given directory
./autogen.sh
./configure --prefix "$BUILDDIR"
make
make install

# Update config
sed -i'' -e "s/^db_nav\s*=\s*nav/db_nav=$PGDATABASE/" "$BUILDDIR/etc/db.conf"
sed -i'' -e "s/^script_default\s*=\s*nav/script_default=$PGUSER/" "$BUILDDIR/etc/db.conf"
sed -i'' -e "s/^userpw_nav\s*=.*/userpw_$PGUSER=$PGPASSWORD/" "$BUILDDIR/etc/db.conf"

if [ -n "$PGHOST" ];        then sed -i'' -e "s/^dbhost\s*=\s*localhost/dbhost=$PGHOST/" "$BUILDDIR/etc/db.conf"; fi
if [ -n "$ADMINPASSWORD" ]; then psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'"; fi
