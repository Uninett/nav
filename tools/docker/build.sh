#!/bin/bash

set -e

if [[ ! -f "/source/setup.py" ]]; then
  echo NAV source code does not appear to be mounted at /source
  exit 1
fi

cd /source
sudo -u nav python3 setup.py build
python3 setup.py develop
sudo -u nav python3 setup.py build_sass

if [[ ! -f "/etc/nav/nav.conf" ]]; then
    echo "Copying initial NAV config files into this container"
    nav config install --verbose /etc/nav
    # Generate fresh JWT keys
    ssh-keygen -t rsa -b 4096 -m PEM -f /etc/nav/api/jwtRS256.key -N ""
    openssl rsa -in /etc/nav/api/jwtRS256.key -pubout -outform PEM -out /etc/nav/api/jwtRS256.key.pub
    chown -R nav:nav /etc/nav
    cd /etc/nav
    sed -e 's/^#\s*\(DJANGO_DEBUG.*\)$/\1/' -i nav.conf  # Enable django debug.
    sed -e 's/^NAV_USER\s*=.*/NAV_USER=nav/' -i nav.conf  # Set the nav user
    sed -e 's/dbhost=.*/dbhost=postgres/g' -i db.conf  # Set nav as db password.
    sed -e 's/userpw_nav=.*/userpw_nav=nav/g' -i db.conf  # Set nav as db password.

    cp /source/tools/docker/graphite.conf /etc/nav/graphite.conf
fi
