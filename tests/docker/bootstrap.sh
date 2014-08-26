#!/bin/bash -xe

# Sneakily modify the build user to match the UID/GID of the real user who owns
# the mounted /source volume.
uid=$(stat -c '%u' /source)
gid=$(stat -c '%g' /source)
usermod --uid "$uid" build
groupmod --gid "$gid" build

mkdir -p /build
chown build:build /build

exec su -c /source/tests/docker/test.sh build
