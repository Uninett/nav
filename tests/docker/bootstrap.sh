#!/bin/bash -xe
umask 0022

# Sneakily modify the build user to match the UID/GID of the real user who owns
# the mounted /source volume - but only if we are running as root
if [ "$EUID" -eq "0" ]; then
    uid=$(stat -c '%u' /source)
    gid=$(stat -c '%g' /source)
    usermod --uid "$uid" build
    groupmod --non-unique  --gid "$gid" build
fi


export WORKSPACE="/source"
export BUILDDIR="${WORKSPACE}/build"
export PYTHONPATH="${WORKSPACE}/python"


if [ -z "$@" ]; then
    echo Nothing to do
    exit 1
else
    # If we're running as root, run stuff as the build user instead
    if [ "$EUID" -eq "0" ]; then
	su -c "$*" build
    else
	"$*" build
    fi
    echo All done.

fi
