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

    # Add non-ASCII chars to the admin user's login name to test encoding
    # compliance for all Cheetah based web pages.
    gosu postgres:postgres psql -c "UPDATE account SET name = 'Administrator ÆØÅ' WHERE login = 'admin'" nav

    # Add some non-ASCII test data to reveal more potential problems during
    # the shift to Python 3
    gosu postgres:postgres psql -c "INSERT INTO location (locationid) VALUES ('bø');" nav
    gosu postgres:postgres psql -c "INSERT INTO room (roomid, locationid) VALUES ('bø-123', 'bø');" nav
}

PGVERSION=$(gosu root pg_lsclusters -h|awk '{print $1}')
gosu root pg_dropcluster --stop ${PGVERSION} main || true
gosu root pg_createcluster --locale=C.UTF-8 --start ${PGVERSION} main -- --nosync

update_nav_db_conf
create_nav_db
