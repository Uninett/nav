#!/bin/bash

set -ex

# Ensure latest NAV code is built
mydir=$(dirname $0)
"$mydir/build.sh"

"$mydir/syncdb.sh" || exit

# Start supervisor to control the rest of the runtime
[[ -f /source/tools/docker/supervisord.conf ]] && \
  sudo cp /source/tools/docker/supervisord.conf /etc/supervisor/conf.d/nav.conf
exec sudo -E /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
