#!/bin/bash -e
# Rebuilds Sphinx documentation on changes
#
cd /source
# Build once first
python setup.py develop
sudo -u nav python setup.py build_sphinx
# Then re-build on any changes to the doc directory
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/doc
do
  sudo -u nav python setup.py build_sphinx
done
