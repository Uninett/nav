#!/bin/bash

# Run necessary daemons
cron
pg_ctlcluster 9.1 main start

# Ensure latest NAV code is built
mydir=$(dirname $0)
"$mydir/build.sh"

# Ensure db schema is up to date
cd /source
sudo -u postgres psql -l | grep -q nav || su postgres -c 'sql/syncdb.py -c'
sudo -u nav sql/syncdb.py -o

# Start dependencies
sudo -u graphite /opt/graphite/bin/carbon-cache.py start
apache2ctl start

# Start NAV
bin/nav start

# Watch SASS files continually for changes and compile new stylesheets if necessary
cd htdocs/
sudo -u nav sass --watch sass:static/css
