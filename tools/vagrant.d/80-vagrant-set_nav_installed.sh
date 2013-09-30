#!/usr/bin/env sh

if [ "$1" != 0 ]; then
  touch ~vagrant/nav_installed || exit 2
fi
