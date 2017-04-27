#!/bin/bash -xe

start_apache() {
    APACHE_CONFIG="${WORKSPACE}/tests/docker/apache.conf"

    echo -n "Starting apache..."
    sudo a2dismod cgid
    /usr/sbin/apache2ctl -f $APACHE_CONFIG -k start
    echo " done"
    wait
}

start_xvfb() {
    XVFB=/usr/bin/Xvfb
    XVFBARGS=":99 -screen 0 1024x768x24 -fbdir /var/tmp -ac"
    PIDFILE="/var/tmp/xvfb.pid"

    echo -n "Starting Xvfb..."
    /sbin/start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $XVFB -- $XVFBARGS
    echo " done"
}


init_db() {
    . /source/tests/docker/create-db.sh
}

run_pytests() {
    /python-unit-tests.sh
    /integration-tests.sh
    /functional-tests.sh
    echo Python tests are done
}

run_jstests() {
    /javascript-tests.sh
}

run_pylint() {
    time "/pylint.sh" > "${WORKSPACE}/pylint.txt"
}

dump_possibly_relevant_apache_accesses() {
    set +x
    ACCESSLOG="${BUILDDIR}/var/log/apache2-access.log"
    if [ -e "$ACCESSLOG" ]; then
        echo "Potentially relevant 40x errors from Apache logs:"
	echo "-------------------------------------------------"
	grep " 40[34] " "$ACCESSLOG"
	echo "-------------------------------------------------"
    fi
}


# MAIN EXECUTION POINT
cd "$WORKSPACE"
/build.sh

run_pylint &
/count-lines-of-code.sh &

init_db
/start-services.sh
trap dump_possibly_relevant_apache_accesses EXIT

run_pytests
run_jstests


echo "Waiting for background tasks to end"
wait

echo "test.sh done"
