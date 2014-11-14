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


if [ -z "$@" ]; then
    echo Nothing to do
    exit 1
else

    su -c "$*" build
    echo All done.

fi
