#!/bin/sh -xe

# Lints the NAV Python source code tree using PyLint with parseable output

cd "${WORKSPACE}"
echo "Running pylint"
export PYLINTHOME="${WORKSPACE}"
pylint python/nav --jobs=4 --rcfile=python/pylint.rc --disable=I,similarities --output-format=parseable || true
