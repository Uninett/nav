#!/bin/bash

NAV_ROOT="/usr/local/nav"

echo -n "Stopping getDeviceData..."
if [ -f $NAV_ROOT/local/var/run/getDeviceData.pid ]; then
  kill `cat $NAV_ROOT/local/var/run/getDeviceData.pid`
  rm -f $NAV_ROOT/local/var/run/getDeviceData.pid
  echo "OK"
else
  echo "Not running"
fi
