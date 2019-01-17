#!/bin/bash
if [ "$EUID" == "0" ]; then
    # Sneakily modify the nav user to match the UID/GID of the real user who owns
    # the mounted /source volume.
    uid=$(stat -c '%u' /source)
    gid=$(stat -c '%g' /source)
    # stuff appears like it's owned by root on OSX host, but is still accessible
    if [ "$uid" -ne 0 ]; then
	usermod --uid "$uid" nav
	groupmod --gid "$gid" nav
    fi
fi

exec "$@"
