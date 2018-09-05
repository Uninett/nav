#!/bin/bash
# Remap the container's build user entry to the currently running UID
gosu root usermod -u $UID build
if [ -n "$WORKSPACE" ]; then
    export HOME="$WORKSPACE"
fi
mkdir -p "$HOME/.cache/pip"
gosu root mkdir -p /usr/share/nav ; gosu root chown build /usr/share/nav
exec "$@"
