#!/bin/bash -xe

# MAIN EXECUTION POINT
cd "$WORKSPACE"
tox run

echo "test.sh done"
