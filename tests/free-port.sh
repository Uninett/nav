#!/bin/bash
# Helper script for Hudson CI setup
# Prints a random port number > 9000 that appears to be unused.
# Is only confirmed to work on a Debian system.
#
BASE=9000
RANGE=5000

randport() {
  echo -e $((RANDOM % $RANGE + $BASE))
}

PORT=$(randport)
USED_PORTS=$(netstat -atn|awk '/^tcp/ {print $4}'| sed 's/^.*://' | sort -n | uniq)

while (echo $USED_PORTS | grep -q $PORT);
do
	PORT=$(randport)
done
echo $PORT
