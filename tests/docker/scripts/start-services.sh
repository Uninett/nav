#!/bin/sh -xe
# Starts services needed for full test suite

start_apache() {
    APACHE_CONFIG="${WORKSPACE}/tests/docker/apache.conf"

    echo -n "Starting apache..."
    gosu root:root a2dismod cgid
    gosu root /usr/sbin/apache2ctl -f $APACHE_CONFIG -k start
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

(start_apache)  # run in subprocess b/c of call to wait
#start_xvfb
