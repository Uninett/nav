#!/bin/bash -xe

# Lints the NAV Python source code tree and outputs a parseable report file in
# the $WORKSPACE

cd "${WORKSPACE}"
echo "Running pylint"
exec pylint python/nav --rcfile=python/pylint.rc --disable=I,similarities --output=parseable
