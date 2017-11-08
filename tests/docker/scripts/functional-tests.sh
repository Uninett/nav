#!/bin/sh -xe
cd "${WORKSPACE}/tests"

export TARGETHOST="localhost"
export APACHE_PORT=8000
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

py.test --junitxml=functional-results.xml \
        --verbose \
        --driver Firefox \
        --driver-path=/usr/local/bin/geckodriver \
        --base-url "$TARGETURL" \
        --sensitive-url "nothing to see here" \
        --html functional-report.html \
        functional
