#!/bin/bash -xe

check_for_postgres() {
    local ver
    if ! which initdb; then
	echo PostgreSQL commands not found on path, looking for them
	for ver in 9.1 9.2 9.3; do
	    PATH="/usr/lib/postgresql/$ver/bin:$PATH"
	done
	export PATH
    fi
    (which initdb && which pg_ctl) || return 1
}

bootstrap_postgres_in_ram() {
    # Run a PostgreSQL cluster in ram
    local ram_mount="/dev/shm"
    local datadir="pg-${EXECUTOR_NUMBER:-$$}"

    PGDATA="$ram_mount/$datadir"
    PGPORT=5432
    if [ -z "$PGPORT" ]; then
	    echo "No PGPORT set"
	    exit 1
    fi
    PGHOST=localhost
    PGUSER=${USER:-postgres}

    PGDATABASE=nav
    PGPASSWORD="notused"
    export PGDATA PGPORT PGHOST PGUSER PGDATABASE PYTHONPATH PGPASSWORD

    test -e "$PGDATA" && rm -rf "$PGDATA"
    initdb -E UTF8

    # Ensure the cluster will run on our selected port
    sed -i'' -e "s/^#\?port *=.*/port=$PGPORT/" "$PGDATA/postgresql.conf"
    sed -i'' -e "s,^#\?#unix_socket_directory *=.*,unix_socket_directory='$PGDATA'," "$PGDATA/postgresql.conf"
    sed -i'' -e "s,^#\?#listen_addresses *=.*,listen_addresses='*'," "$PGDATA/postgresql.conf"
    sed -i'' -e "s,^#\?#fsync *=.*,fsync=off," "$PGDATA/postgresql.conf"

    PGCTL=$(which pg_ctl)
    export PGCTL
    "$PGCTL" start -w -o '-i'

    # Just print out the current PG* environment
    env|grep ^PG
    return 0
}


update_nav_db_conf() {

    # Update db config
    sed -i'' -e "s,^db_nav\s*=\s*nav,db_nav=$PGDATABASE," "$BUILDDIR/etc/db.conf"
    sed -i'' -e "s/^script_default\s*=\s*nav/script_default=$PGUSER/" "$BUILDDIR/etc/db.conf"
    sed -i'' -e "s/^userpw_nav\s*=.*/userpw_$PGUSER=$PGPASSWORD/" "$BUILDDIR/etc/db.conf"
    if [ -n "$PGHOST" ]; then sed -i'' -e "s/^dbhost\s*=\s*localhost/dbhost=$PGHOST/" "$BUILDDIR/etc/db.conf"; fi
    if [ -n "$PGPORT" ]; then sed -i'' -e "s/^dbport\s*=.*/dbport=$PGPORT/" "$BUILDDIR/etc/db.conf"; fi
}


create_nav_db() {

    # Create and populate database
    "$BUILDDIR/bin/navsyncdb" -c

    if [ -n "$ADMINPASSWORD" ]; then
      psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'";
    fi

    # Add non-ASCII chars to the admin user's login name to test encoding
    # compliance for all Cheetah based web pages.
    psql -c "UPDATE account SET name = 'Administrator ÆØÅ' WHERE login = 'admin'"
}

check_for_postgres
bootstrap_postgres_in_ram
update_nav_db_conf
create_nav_db
