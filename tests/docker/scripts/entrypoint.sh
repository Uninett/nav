#!/bin/bash
# Remap the container's build user entry to the currently running UID
gosu root usermod -u $UID build
if [ -n "$WORKSPACE" ]; then
    export HOME="$WORKSPACE"
fi
mkdir -p "$HOME/.cache/pip"
exec "$@"
