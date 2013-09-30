#!/usr/bin/env bash
#
# Helper script to allow quick setup of a full NAV environment for integration
# testing
#
set -e

# Always default to using system site packages in virtualenv
test -z "$USE_SYSTEM_PACKAGES" && USE_SYSTEM_PACKAGES=1
HGROOT=$(hg root)
WORKDIR=${1:-${HGROOT:-$PWD}}

BUILDDIR="$WORKDIR/build"
VIRTENV="$WORKDIR/.env"

#################
# Trap handling #
#################

EXITTRAPS=()
call_exittraps() {
    for (( i=0; i<${#EXITTRAPS[*]}; i++))
    do
	${EXITTRAPS[$i]}
    done
}

append_trap() {
    EXITTRAPS+=("$@")
}

prepend_trap() {
    EXITTRAPS=("$@" "${EXITTRAPS[@]}")
}

trap -- 'call_exittraps' EXIT

####################
# Helper functions #
####################

clear_build_directory() {
    test -d "$BUILDDIR" && rm -rf "$BUILDDIR"
}

init_virtenv() {
    # Create and activate virtualenv for some required python packages, and keep
    # it around to avoid hitting the network each time a job runs.
    local virtenv="${1:-$VIRTENV}"
    if [ -d "$virtenv" ]; then
	echo "**> virtualenv exists"
    else
	echo "**> creating virtualenv"
	opt=
	test -n "$PYTHON_VER" && opt="-p python$PYTHON_VER"
	if virtualenv --help 2>&1 | grep -q -- --system-site-packages; then
	    # this virtualenv binary appears to not use system site pkgs by default
	    test "$USE_SYSTEM_PACKAGES" != 0 && opt="$opt --system-site-packages"
	else
	    test "$USE_SYSTEM_PACKAGES" = 0 && opt="$opt --no-site-packages"
	fi
	virtualenv $opt "$virtenv"
    fi
    . "$virtenv/bin/activate"
    pip install -r tests/requirements.txt
}

install_nav() {
    # Install everything into the $BUILDDIR to test if the full build system works
    ./autogen.sh
    ./configure --prefix "$BUILDDIR"
    make
    make install

    export PYTHONPATH="$BUILDDIR/lib/python"
}

enable_nav_debug() {
    cat > "$BUILDDIR/etc/logging.conf" <<EOF
[levels]
root=DEBUG
EOF
}

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
    PGPORT=$($WORKDIR/tests/free-port.sh)
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
    initdb && append_trap "rm -rf $PGDATA"

    # Ensure the cluster will run on our selected port
    sed -i'' -e "s/^#\?port *=.*/port=$PGPORT/" "$PGDATA/postgresql.conf"
    sed -i'' -e "s,^#\?#unix_socket_directory *=.*,unix_socket_directory='$PGDATA'," "$PGDATA/postgresql.conf"

    PGCTL=$(which pg_ctl)
    "$PGCTL" start && prepend_trap "$PGCTL stop"

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

bootstrap_apache() {
    if [ -z "$APACHE_CONFIG" ]; then
	echo Environment variable APACHE_CONFIG must be set
	return 1
    elif ! [ -f "$APACHE_CONFIG" ]; then
	echo "$APACHE_CONFIG does not exist"
	return 1
    fi

    export TARGETHOST=$(hostname -f)
    export APACHE_PORT=$($WORKDIR/tests/free-port.sh)
    export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

    . "$VIRTENV/bin/activate"

    /usr/sbin/apache2ctl -f $APACHE_CONFIG  -k start
    prepend_trap "/usr/sbin/apache2ctl -f $APACHE_CONFIG  -k stop"

    GET ${TARGETURL} # just to make sure we can get at it
}

########################
# Main execution point #
########################

cd $WORKDIR
init_virtenv
check_for_postgres
bootstrap_postgres_in_ram
install_nav
enable_nav_debug
update_nav_db_conf
create_nav_db
bootstrap_apache
