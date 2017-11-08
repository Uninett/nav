#!/bin/sh -xe
cd "${WORKSPACE}"
CHROME_BIN=$(which google-chrome) ./tests/javascript-test.sh "$(pwd)"
