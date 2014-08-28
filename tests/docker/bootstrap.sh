#!/bin/bash -xe
umask 0022

# Sneakily modify the build user to match the UID/GID of the real user who owns
# the mounted /source volume.
uid=$(stat -c '%u' /source)
gid=$(stat -c '%g' /source)
usermod --uid "$uid" build
groupmod --gid "$gid" build


export WORKSPACE="/source"
export BUILDDIR="${WORKSPACE}/build"
export PYTHONPATH="${WORKSPACE}/python"

start_apache() {
    APACHE_CONFIG="${WORKSPACE}/tests/apache.conf"

    echo -n "Starting apache..."
    a2dismod cgid
    /usr/sbin/apache2ctl -f $APACHE_CONFIG -k start
    echo " done"
}

start_xvfb() {
    XVFB=/usr/bin/Xvfb
    XVFBARGS=":99 -screen 0 1024x768x24 -fbdir /var/tmp -ac"
    PIDFILE="/var/tmp/xvfb.pid"

    echo -n "Starting Xvfb..."
    sudo -u build -- /sbin/start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $XVFB -- $XVFBARGS
    echo " done"
}

if [ -z "$@" ]; then
    echo Nothing to do
    exit 1
fi

start_apache
start_xvfb

su -c "$*" build

echo Done.
