#!/usr/bin/env bash
# Builds a virtual appliance in OVF format out of NAV, based on Debian Wheezy
# and the latest available NAV Debian package.
PACKER="$(which packer)"
if [ -z "$PACKER" ]; then
    echo You need to install packer to to build the virtual appliance.
    echo Pleae see http://www.packer.io/
else
    "$PACKER" build nav-debian-virtual-appliance.json
fi

