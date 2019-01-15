#!/usr/bin/env bash
# ensures Apache restarts the WSGI process on changes to /source/python
#
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/python
do
  supervisorctl restart web
done
