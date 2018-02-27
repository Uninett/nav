#!/bin/bash -xe

run_pylint() {
    time "/pylint.sh" > "${WORKSPACE}/pylint.txt"
}


# MAIN EXECUTION POINT
cd "$WORKSPACE"
tox

# Code analysis steps
run_pylint
/count-lines-of-code.sh

echo "test.sh done"
