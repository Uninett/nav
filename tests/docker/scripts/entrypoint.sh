#!/bin/bash
# Remap the container's build user entry to the currently running UID
gosu root usermod -u $UID build
gosu root chown -R $UID /home/build
export PYTHONPATH="$WORKSPACE/python"
exec "$@"
