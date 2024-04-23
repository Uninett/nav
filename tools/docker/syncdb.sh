#!/bin/bash -ex
cd /source
export PGHOST=postgres PGUSER=postgres
psql -l -t | grep -q '^ *nav' || navsyncdb -c
navsyncdb -o
