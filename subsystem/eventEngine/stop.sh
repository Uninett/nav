#!/bin/bash

NAV_ROOT="/usr/local/nav"
#NAV_ROOT="/home/kristian/devel"

echo -n "Stopping eventEngine..."
if [ -f $NAV_ROOT/local/var/run/eventEngine.pid ]; then
  kill `cat $NAV_ROOT/local/var/run/eventEngine.pid`
  rm -f $NAV_ROOT/local/var/run/eventEngine.pid
  echo "OK"
else
  echo "Not running"
fi
