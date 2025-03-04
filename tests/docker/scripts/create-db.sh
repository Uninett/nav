#!/bin/bash -xe
# Creates and initializes a NAV database for the test runner

maybesudo() {
    # Run command using gosu or sudo, unless we're running on GitHub Actions
    user="$1"
    shift
    if [ -n "$GITHUB_ACTIONS" ]; then
        $@
    else
        sudo -u "$user" $@
    fi
}

update_nav_db_conf() {
    # Update db config
    DBCONF="${BUILDDIR}/etc/db.conf"
    echo "Updating $DBCONF"
    maybesudo root tee "$DBCONF" <<EOF
dbhost=${PGHOST:-localhost}
dbport=${PGPORT:-5432}
db_nav=${PGDATABASE}
script_default=${PGUSER:-nav}
userpw_${PGUSER:-nav}=${PGPASSWORD:-notused}
EOF
}


create_nav_db() {

    # Create and populate database
    echo Creating and populating initial database
    maybesudo postgres "${BUILDDIR}/bin/navsyncdb" -c --drop-database

    if [ -n "$ADMINPASSWORD" ]; then
      maybesudo postgres psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'" $PGDATABASE
    fi

    # Add generic test data set
    maybesudo postgres psql -f "$(dirname $0)/test-data.sql" $PGDATABASE

}

if [ -z "$GITHUB_ACTIONS" ]; then
    # If not on GitHub actions, we manipulate PostgreSQL clusters directly
    PGVERSION=$(sudo pg_lsclusters -h|awk '{print $1}')
    export PGDATABASE=nav
    sudo pg_dropcluster --stop ${PGVERSION} main || true
    sudo pg_createcluster --locale=C.UTF-8 --start ${PGVERSION} main -- --nosync
else
    # Generate an appropriately unique database name for this test run
    if [ -z "$PGDATABASE" ] && [ -n "$TOX_ENV_NAME" ]; then
        export PGDATABASE=${GITHUB_RUN_ID:-tox}_$(echo $TOX_ENV_NAME | tr '-' '_')
    else
        export PGDATABASE=nav
    fi
fi

update_nav_db_conf
create_nav_db
