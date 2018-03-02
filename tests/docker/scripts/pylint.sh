#!/bin/sh
# invoke pylint w/args and send stdout to a report file
# pylint has weird exit codes, so ignore those.
pylint "$@" > reports/pylint.txt || true
