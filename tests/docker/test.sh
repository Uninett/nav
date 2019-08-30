#!/bin/bash -xe

# MAIN EXECUTION POINT
cd "$WORKSPACE"
tox

# Code analysis steps
tox -e pylint
/count-lines-of-code.sh

echo "test.sh done"
