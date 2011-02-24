#!/bin/sh
# Helper script for Hudson CI setup
# Prints the system's first free port > 9000
# Is only confirmed to work on a Debian system.
#
PORT=9000
USED_PORTS=$(netstat -atn|awk '/LISTEN/ {print $4}'| sed 's/^.*://' | sort -n | uniq)

while (echo $USED_PORTS | grep -q $PORT);
do
	PORT=$(expr $PORT + 1)
done
echo $PORT
