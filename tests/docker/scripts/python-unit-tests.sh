#!/bin/sh -xe
cd "${WORKSPACE}/tests"
py.test --cov=/opt/nav/lib/python --cov-report=xml:coverage.xml --junitxml=unit-results.xml --verbose unittests
sed -i 's!filename="nav/!filename="python/nav/!' coverage.xml
