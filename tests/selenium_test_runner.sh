#!/bin/bash
if [ ! -n "$1" ]; then
    echo "Need targeturl"
    exit 1
fi

export TARGETURL=$1

source start_xvfb.sh
py.test --junitxml=selenium-results.xml functional


if [ "$?" -eq 1 ]; then
    echo "Error when testing, taking screenshot"
    import -window root ${WORKSPACE}/tests/selenium-test-error.png
fi
