#!/bin/bash -xe
umask 0022


install_nav() {

    echo "Building an installing NAV..."
    ./autogen.sh
    ./configure --prefix "$BUILDDIR"
    make
    make install
    cat > "$BUILDDIR/etc/logging.conf" <<EOF
[levels]
root=DEBUG
EOF
    echo " done"
}

start_apache() {

    APACHE_CONFIG="$(pwd)/tests/apache.conf"
    export APACHE_CONFIG
    export WORKSPACE="$(pwd)"
    export TARGETHOST="localhost"
    export APACHE_PORT=80
    export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

    echo -n "Starting apache..."
    /usr/sbin/apache2ctl -f $APACHE_CONFIG -k start
    echo " done"
}

start_xvfb() {

    XVFB=/usr/bin/Xvfb
    XVFBARGS=":99 -screen 0 1024x768x24 -fbdir /tmp -ac"
    PIDFILE=/tmp/xvfb.pid

    echo -n "Starting Xvfb..."
    /sbin/start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $XVFB -- $XVFBARGS
    echo " done"
    x11vnc -passwd 1234 &
}

cd /source
BUILDDIR="/build"
export PYTHONPATH="$BUILDDIR/lib/python"

install_nav
start_xvfb
./tests/docker/create-db.sh
start_apache

# Tests
echo "Running tests"
export TARGETHOST="localhost"
export APACHE_PORT=80
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

cd tests
py.test --junitxml=unit-results.xml --verbose unittests
py.test --junitxml=integration-results.xml --verbose integration functional

# JS tests
cd ..
CHROME_BIN=$(which google-chrome) ./tests/javascript-test.sh "$(pwd)"

# Pylint
echo "Running pylint"
pylint python/nav --rcfile=python/pylint.rc --disable=I,similarities --output=parseable > pylint.txt || true
