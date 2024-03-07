#!/bin/bash -e
# Rebuilds Sphinx documentation on changes
#
cd /source
# Build once first
sudo -u nav env PATH=$PATH python3 -m build  # ensure build data and .eggs aren't stored as root
pip install -e .
sudo -u nav env PATH=$PATH sphinx-build doc/ build/sphinx/html/
# Then re-build on any changes to the doc directory
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/doc /source/NOTES.rst
do
  sudo -u nav env PATH=$PATH sphinx-build doc/ build/sphinx/html/
done
