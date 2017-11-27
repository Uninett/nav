#!/bin/sh -xe
cd "${WORKSPACE}/tests"

export TARGETHOST="localhost"
export APACHE_PORT=8000
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

py.test \
    --cov=/opt/nav/lib/python --cov-append --cov-report=xml:coverage.xml\
    --junitxml=integration-results.xml \
    --html integration-report.html \
    --verbose --twisted \
    integration
sed -i 's!filename="nav/!filename="python/nav/!' coverage.xml
