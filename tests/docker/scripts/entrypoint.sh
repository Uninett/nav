#!/bin/bash
# Remap the container's build user entry to the currently running UID
gosu root usermod -u $UID build
mkdir -p /source/.cache/pip
exec "$@"
