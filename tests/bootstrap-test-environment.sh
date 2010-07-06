#!/bin/sh
set -e

test -z "$PGDATABASE" && echo PGDATABASE missing && exit 1
test -z "$PGUSER"     && echo PGUSER missing     && exit 1
test -z "$1"          && echo dir missing        && exit 1

# Create virualenv for installing nose
virtualenv "$1"
source "$1/bin/activate"
easy_install nose

# Cleanup any existing DB
dropdb $PGDATABASE || true

(cd doc/sql; ./createdb.sh -d $PGDATABASE -u $PGUSER -U)

# Clear directory
test -e "$1" && rm -rf "$1"

# Make install code into given directory
./autogen.sh
./configure --prefix "$1"
make
make install

# Update config
sed -i'' -e "s/^db_nav\s*=\s*nav/db_nav=$PGDATABASE/" "$1/etc/db.conf"
sed -i'' -e "s/^script_default\s*=\s*nav/script_default=$PGUSER/" "$1/etc/db.conf"
sed -i'' -e "s/^userpw_nav\s*=.*/userpw_$PGUSER=$PGPASSWORD/" "$1/etc/db.conf"

if [ -n "$PGHOST" ];        then sed -i'' -e "s/^dbhost\s*=\s*localhost/dbhost=$PGHOST/" "$1/etc/db.conf" fi
if [ -n "$ADMINPASSWORD" ]; then psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'"; fi
