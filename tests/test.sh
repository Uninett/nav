#!/bin/bash

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
    XVFBARGS=":99 -screen 0 1024x768x24 -fbdir /var/run -ac"
    PIDFILE=/var/run/xvfb.pid

    echo -n "Starting Xvfb..."
    start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $XVFB -- $XVFBARGS
    echo " done"
}

cd source
chmod 777 -R .
BUILDDIR="$(pwd)/build"
export PYTHONPATH="$BUILDDIR/lib/python"

install_nav
start_xvfb
(su postgres -c './tests/create-db.sh')
start_apache

# Sync
wait

# Pylint
echo "Running pylint"
pylint nav --rcfile=python/pylint.rc --disable=I,similarities --output=parseable > pylint.txt || true

# Tests
echo "Running tests"
export TARGETHOST="localhost"
export APACHE_PORT=80
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

cd tests; py.test --junitxml=test-results.xml --verbose .

# JS tests
cd ..
curl --insecure https://www.npmjs.org/install.sh | clean=no bash
CHROME_BIN=$(which chromium) ./tests/javascript-test.sh "$(pwd)"