#!/bin/bash -ex
# Rebuilds Sphinx documentation on changes
#
cd /source
# Build once first
pip install -e .
sphinx-build doc/ build/sphinx/html/
# Then re-build on any changes to the doc directory
while inotifywait -e modify -e move -e create -e delete -r --exclude \# /source/doc /source/NOTES.rst
do
  sphinx-build doc/ build/sphinx/html/
done
