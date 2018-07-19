#!/bin/bash -e
cd /source
export PGHOST=postgres PGUSER=postgres
psql -l | grep -q nav || navsyncdb -c
sudo -u nav navsyncdb -o
