#!/usr/bin/env bash
# Builds a virtual appliance in OVF format out of NAV, based on Debian Wheezy
# and the latest available NAV Debian package.

TARBALL=nav-virtual-appliance.tar.gz
PACKER="$(which packer)"
if [ -z "$PACKER" ]; then
    echo You need to install packer to to build the virtual appliance.
    echo Pleae see http://www.packer.io/
    exit 1
fi

"$PACKER" build nav-debian-virtual-appliance.json
tar cvzf "$TARBALL" nav-virtual-appliance/
gpg --armor --detach-sign "$TARBALL"
