#!/bin/bash -xe

# MAIN EXECUTION POINT
cd "$WORKSPACE"
tox run

# Code analysis steps
tox run -e pylint
/count-lines-of-code.sh

echo "test.sh done"
