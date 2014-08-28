#!/bin/bash -xe
umask 0022


install_nav() {

    echo "Building an installing NAV..."
    ./autogen.sh
    ./configure --prefix "$BUILDDIR" NAV_USER=build
    make
    make install
    cat > "$BUILDDIR/etc/logging.conf" <<EOF
[levels]
root=DEBUG
EOF
    echo " done"
}

start_apache() {
    APACHE_CONFIG="/source/tests/apache.conf"

    echo -n "Starting apache..."
    sudo a2dismod cgid
    /usr/sbin/apache2ctl -f $APACHE_CONFIG -k start
    echo " done"
}

start_xvfb() {
    XVFB=/usr/bin/Xvfb
    XVFBARGS=":99 -screen 0 1024x768x24 -fbdir /build -ac"
    PIDFILE=/build/xvfb.pid

    echo -n "Starting Xvfb..."
    /sbin/start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $XVFB -- $XVFBARGS
    echo " done"
}

cd /source
BUILDDIR="/build"
export PYTHONPATH="$BUILDDIR/lib/python"

install_nav

# Tests
echo "Running tests"
export TARGETHOST="localhost"
export APACHE_PORT=8000
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

/source/tests/docker/create-db.sh

cd tests
py.test --junitxml=unit-results.xml --verbose unittests

cd ..

start_apache

cd tests
py.test --junitxml=integration-results.xml --verbose integration

start_xvfb
py.test --junitxml=functional-results.xml --verbose functional

echo Python tests are done

# JS tests
cd ..
CHROME_BIN=$(which google-chrome) ./tests/javascript-test.sh "$(pwd)"

# Pylint
echo "Running pylint"
pylint python/nav --rcfile=python/pylint.rc --disable=I,similarities --output=parseable > pylint.txt || true
