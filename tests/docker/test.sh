#!/bin/bash -xe

build_nav() {
    cd "${WORKSPACE}"

    echo "Building and installing NAV..."
    ./autogen.sh
    ./configure --prefix "${BUILDDIR}" NAV_USER=build
    make
    make install
    cat > "${BUILDDIR}/etc/logging.conf" <<EOF
[levels]
root=DEBUG
EOF
}

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
    /source/tests/docker/create-db.sh
}

run_pytests() {
    export TARGETHOST="localhost"
    export APACHE_PORT=8000
    export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

    cd "${WORKSPACE}/tests"
    py.test --junitxml=unit-results.xml --verbose unittests
    py.test --junitxml=integration-results.xml --verbose integration
    py.test --junitxml=functional-results.xml --verbose functional

    echo Python tests are done
}

run_jstests() {
    cd "${WORKSPACE}"
    CHROME_BIN=$(which google-chrome) ./tests/javascript-test.sh "$(pwd)"
}

run_pylint() {
    cd "${WORKSPACE}"
    echo "Running pylint"
    pylint python/nav --rcfile=python/pylint.rc --disable=I,similarities --output=parseable > pylint.txt || true
}

# MAIN EXECUTION POINT
build_nav

init_db
start_apache
start_xvfb

run_pytests
run_jstests
run_pylint

echo "test.sh done"
