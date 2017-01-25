#!/bin/bash

set -e

# Ensure latest NAV code is built
mydir=$(dirname $0)
"$mydir/build.sh"

mkdir -p /var/run/apache2
rm -f /var/run/apache2/*.pid

"$mydir/syncdb.sh" || exit

# Start supervisor to control the rest of the runtime
[[ -f /source/tools/docker/supervisord.conf ]] && \
  cp /source/tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
