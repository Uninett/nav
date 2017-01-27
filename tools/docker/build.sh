#!/bin/bash

set -e

if [[ ! -x "/source/autogen.sh" ]]; then
  echo NAV source code does not appear to be mounted at /source
  exit 1
fi

# Sneakily modify the nav user to match the UID/GID of the real user who owns
# the mounted /source volume.
uid=$(stat -c '%u' /source)
gid=$(stat -c '%g' /source)
# stuff appears like it's owned by root on OSX host, but is still accessible
if [ "$uid" -ne 0 ]; then
    usermod --uid "$uid" nav
    groupmod --gid "$gid" nav
fi

cd /source
sudo -u nav ./autogen.sh
sudo -u nav ./configure NAV_USER="nav" --disable-install-conf --prefix /source --localstatedir /var/lib/nav --sysconfdir /etc/nav --datadir /source --libdir /source
sudo -u nav make

if [[ ! -d "/etc/nav" ]]; then
    cd /source/etc
    sudo -u nav make clean
    sudo -u nav make
    make install
    cd /etc/nav
    sed -e 's/^#\s*\(DJANGO_DEBUG.*\)$/\1/' -i nav.conf  # Enable django debug.
    sed -e 's/dbhost=.*/dbhost=postgres/g' -i db.conf  # Set nav as db password.
    sed -e 's/userpw_nav=.*/userpw_nav=nav/g' -i db.conf  # Set nav as db password.

    cp /source/tools/docker/graphite.conf /etc/nav/graphite.conf

    cd /source
    make installdirs-local
    chown -R nav:nav /etc/nav
    chown -R nav:nav /var/lib/nav
fi
