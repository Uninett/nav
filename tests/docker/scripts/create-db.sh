#!/bin/bash -xe
update_nav_db_conf() {
    # Update db config
    DBCONF="${BUILDDIR}/etc/db.conf"
    echo "Updating $DBCONF"
    gosu root tee "$DBCONF" <<EOF
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
    gosu postgres:postgres "${BUILDDIR}/bin/navsyncdb" -c

    if [ -n "$ADMINPASSWORD" ]; then
      gosu postgres:postgres psql -c "UPDATE account SET password = '$ADMINPASSWORD' WHERE login = 'admin'" nav
    fi

    # Add generic test data set
    gosu postgres:postgres psql -f "$(dirname $0)/test-data.sql" nav

}

PGVERSION=$(gosu root pg_lsclusters -h|awk '{print $1}')
gosu root pg_dropcluster --stop ${PGVERSION} main || true
gosu root pg_createcluster --locale=C.UTF-8 --start ${PGVERSION} main -- --nosync

update_nav_db_conf
create_nav_db
