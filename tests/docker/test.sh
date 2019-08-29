#!/bin/bash -xe

# MAIN EXECUTION POINT
cd "$WORKSPACE"
tox -e unit-py35-django111 -- tests/unittests/general/web_middleware_test.py::TestEnsureAccount

# Code analysis steps
tox -e pylint
/count-lines-of-code.sh

echo "test.sh done"
