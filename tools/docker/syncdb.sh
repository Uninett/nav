#!/bin/bash -e
cd /source
sudo -u postgres psql -l | grep -q nav || sudo -u postgres sql/syncdb.py -c
sudo -u nav /source/sql/syncdb.py -o
