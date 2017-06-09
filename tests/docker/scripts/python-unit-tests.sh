#!/bin/sh -xe
cd "${WORKSPACE}/tests"
py.test --junitxml=unit-results.xml --verbose unittests
