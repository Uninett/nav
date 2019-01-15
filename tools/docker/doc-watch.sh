#!/usr/bin/env bash
# Rebuilds Sphinx documentation on changes
#
cd /source
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/doc
do
  python setup.py build_sphinx
done
