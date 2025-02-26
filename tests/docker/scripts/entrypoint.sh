#!/bin/bash

# Function to get the owner UID and GID of the /source directory
get_source_uid_gid() {
    stat -c "%u %g" /source
}

# Get the UID and GID of the /source directory
SOURCE_UID_GID=$(get_source_uid_gid)
SOURCE_UID=$(echo "$SOURCE_UID_GID" | cut -d ' ' -f 1)
SOURCE_GID=$(echo "$SOURCE_UID_GID" | cut -d ' ' -f 2)

# Modify the build user's UID and GID to match the /source directory's UID and GID
usermod --non-unique -u $SOURCE_UID build
groupmod --non-unique -g $SOURCE_GID build

if [ -n "$WORKSPACE" ]; then
    export HOME="$WORKSPACE"
fi
mkdir -p "$HOME/.cache/pip" && chown -R build "$HOME/.cache"
mkdir -p /usr/share/nav ; chown build /usr/share/nav

# Execute the command as the build user using gosu
exec gosu build "$@"
