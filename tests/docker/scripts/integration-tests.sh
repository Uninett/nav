#!/bin/sh -xe
cd "${WORKSPACE}/tests"

export TARGETHOST="localhost"
export APACHE_PORT=8000
export TARGETURL=http://$TARGETHOST:$APACHE_PORT/

py.test --junitxml=integration-results.xml \
	--html integration-report.html \
	--verbose \
	integration
