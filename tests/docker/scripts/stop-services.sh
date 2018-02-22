#!/bin/sh -xe
# Stops services started by start-services.sh

stop_apache() {
    APACHE_CONFIG="${WORKSPACE}/tests/docker/apache.conf"

    echo -n "Stopping Apache"
    gosu root /usr/sbin/apache2ctl -f $APACHE_CONFIG -k stop
    echo " done"
}

stop_xvfb() {
    XVFB=/usr/bin/Xvfb
    PIDFILE="/var/tmp/xvfb.pid"

    echo -n "Stopping Xvfb..."
    /sbin/start-stop-daemon --stop --quiet --pidfile $PIDFILE
    echo " done"
}

stop_apache
#stop_xvfb
