#!/bin/sh -e
REMOTE="$1"

if [ -z "$REMOTE" ]; then
    echo "Must give remote SSH host/username combo as argument" >> /dev/stderr
    exit 1
fi
echo "Dumping NAV database from $REMOTE"

# This filters potentially huge amounts of old log data and also user alert
# profiles (so as not to start sending notifications to real users from a dev
# environment):
ssh "$REMOTE" navpgdump --only-open-arp --only-open-cam -e alertprofile -e alerthist
