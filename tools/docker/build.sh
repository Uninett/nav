#!/bin/bash

set -e

if [[ ! -f "/source/setup.py" ]]; then
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
sudo -u nav python setup.py build
python setup.py develop
sudo -u nav python setup.py build_sass

if [[ ! -d "/etc/nav" ]]; then
    echo "Copying initial NAV config files into this container"
    nav config install --verbose /etc/nav
    chown -R nav:nav /etc/nav
    cd /etc/nav
    sed -e 's/^#\s*\(DJANGO_DEBUG.*\)$/\1/' -i nav.conf  # Enable django debug.
    sed -e 's/^NAV_USER\s*=.*/NAV_USER=nav/' -i nav.conf  # Set the nav user
    sed -e 's/dbhost=.*/dbhost=postgres/g' -i db.conf  # Set nav as db password.
    sed -e 's/userpw_nav=.*/userpw_nav=nav/g' -i db.conf  # Set nav as db password.

    cp /source/tools/docker/graphite.conf /etc/nav/graphite.conf
fi
