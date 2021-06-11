#!/bin/bash -xe
# Creates and initializes a NAV database for the test runner

maybesudo() {
    # Run command using gosu or sudo, unless we're running on GitHub Actions
    user="$1"
    shift
    if [ -n "$GITHUB_ACTIONS" ]; then
        $@
    else
        gosu "$user" $@
    fi
}

update_nav_db_conf() {
    # Update db config
    DBCONF="${BUILDDIR}/etc/db.conf"
    echo "Updating $DBCONF"
    maybesudo root tee "$DBCONF" <<EOF
dbhost=${PGHOST:-localhost}
dbport=${PGPORT:-5432}
db_nav=${PGDATABASE:-nav}
script_default=${PGUSER:-nav}
userpw_${PGUSER:-nav}=${PGPASSWORD:-notused}
EOF
}


create_nav_db() {

    # Create and populate database
    echo Creating and populating initial database
    maybesudo postgres:postgres "${BUILDDIR}/bin/navsyncdb" -c --drop-database

    if [ -n "$ADMINPASSWORD" ]; then
      maybesudo postgres:postgres psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'" ${PGDATABASE:-nav}
    fi

    # Add generic test data set
    maybesudo postgres:postgres psql -f "$(dirname $0)/test-data.sql" ${PGDATABASE:-nav}

}

if [ -z "$GITHUB_ACTIONS" ]; then
    # If not on GitHub actions, we manipulate PostgreSQL clusters directly
    PGVERSION=$(gosu root pg_lsclusters -h|awk '{print $1}')
    gosu root pg_dropcluster --stop ${PGVERSION} main || true
    gosu root pg_createcluster --locale=C.UTF-8 --start ${PGVERSION} main -- --nosync
fi

update_nav_db_conf
create_nav_db
