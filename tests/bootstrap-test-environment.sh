#!/bin/sh
#
# Helper script to allow quick setup of a full NAV environment for integration
# testing
#

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
    opt=
    test -n "$PYTHON_VER" && opt="-p python$PYTHON_VER"
    virtualenv $opt "$VIRTENV"
fi
. "$VIRTENV/bin/activate"
easy_install pip || exit 1
pip install -r tests/requirements.txt || exit 1


# Make install code into given directory
./autogen.sh || exit 1
./configure --prefix "$BUILDDIR" || exit 1
make || exit 1
make install || exit 1

export PYTHONPATH="$BUILDDIR/lib/python"

# Update db config
sed -i'' -e "s,^db_nav\s*=\s*nav,db_nav=$PGDATABASE," "$BUILDDIR/etc/db.conf"
sed -i'' -e "s/^script_default\s*=\s*nav/script_default=$PGUSER/" "$BUILDDIR/etc/db.conf"
sed -i'' -e "s/^userpw_nav\s*=.*/userpw_$PGUSER=$PGPASSWORD/" "$BUILDDIR/etc/db.conf"
if [ -n "$PGHOST" ]; then sed -i'' -e "s/^dbhost\s*=\s*localhost/dbhost=$PGHOST/" "$BUILDDIR/etc/db.conf"; fi
if [ -n "$PGPORT" ]; then sed -i'' -e "s/^dbport\s*=.*/dbport=$PGPORT/" "$BUILDDIR/etc/db.conf"; fi

# Remove existing DB, if any, and create new one
dropdb $PGDATABASE || true
sql/syncdb.py -c || exit 1

if [ -n "$ADMINPASSWORD" ]; then psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'"; fi

# Add non-ASCII chars to the admin user's login name to test encoding
# compliance for all Cheetah based web pages.
psql -c "UPDATE account SET name = 'Administrator ÆØÅ' WHERE login = 'admin'"
