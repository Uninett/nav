#!/usr/bin/env bash
# ensures CSS files are rebuilt on SASS file changes
#
cd /source
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/python/nav/web/sass
do
  python3 setup.py build_sass
done
