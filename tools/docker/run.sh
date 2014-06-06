#!/bin/bash

# Ensure latest NAV code is built
mydir=$(dirname $0)
"$mydir/build.sh"

mkdir -p /var/run/apache2
mkdir -p /var/run/sshd

# Start postgresql, update the schema
pg_ctlcluster 9.1 main start
"$mydir/syncdb.sh" || exit

# Start supervisor to control the rest of the runtime
[[ -f /source/tools/docker/supervisord.conf ]] && \
  cp /source/tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf
exec /usr/bin/supervisord
