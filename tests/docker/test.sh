#!/bin/bash -xe
# Tests
echo "Running tests"
export TARGETHOST="localhost"
export APACHE_PORT=8000
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

/source/tests/docker/create-db.sh

cd "${WORKSPACE}/tests"
py.test --junitxml=unit-results.xml --verbose unittests
py.test --junitxml=integration-results.xml --verbose integration
py.test --junitxml=functional-results.xml --verbose functional

echo Python tests are done

# JS tests
cd "${WORKSPACE}"
CHROME_BIN=$(which google-chrome) ./tests/javascript-test.sh "$(pwd)"

# Pylint
echo "Running pylint"
pylint python/nav --rcfile=python/pylint.rc --disable=I,similarities --output=parseable > pylint.txt || true
