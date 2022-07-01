#!/bin/bash -e
# Rebuilds Sphinx documentation on changes
#
cd /source
# Build once first
sudo -u nav python3 setup.py build  # ensure build data and .eggs aren't stored as root
python3 setup.py develop
sudo -u nav python3 setup.py build_sphinx
# Then re-build on any changes to the doc directory
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/doc /source/NOTES.rst
do
  sudo -u nav python3 setup.py build_sphinx
done
