#!/bin/bash
if [ ! -n "$1" ]; then
    echo "Need path to workspace"
    exit 1
fi

SLEEPTIME=8
WORKSPACE=$1
JSDIR="${WORKSPACE}/media/js"

XVFB=`which Xvfb`
if [ "$?" -eq 1 ]; then
    echo "Xvfb not found"
    exit 1
fi

NPM=`which npm`

cd ${JSDIR}
npm install --optional

echo "Running jshint"
JAVASCRIPT_FILES=( $(find ${JSDIR}/src -iname "*.js" -print) )
jshint() {
    local JSHINTDIR=${JSDIR}/node_modules/jshint/bin
    for cmd in hint jshint; do
	if [ -x ${JSHINTDIR}/${cmd} ]; then
	    ${JSHINTDIR}/${cmd} "$@" || true
	    return
	fi
    done
    echo "jshint executable was not found"
}
jshint --config ${JSDIR}/jshint.rc.json ${JAVASCRIPT_FILES[@]} --jslint-reporter > ${JSDIR}/javascript-jshint.xml || true

# Verify that jshint was running as jshint will have non-zero exit if ANY linting errors is found.
[ -s "${JSDIR}/javascript-jshint.xml" ]

echo "Starting Xvfb"
XVFB_TRIES=0
XVFB_STARTED=0
until [ ${XVFB_STARTED} -eq 1 ] || (( ${XVFB_TRIES} > 10 )) ; do
    # Find random display number for Xvfb
    DISPLAYNUM=$((RANDOM%10+90))
    ${XVFB} :${DISPLAYNUM} -screen 0 1280x1024x16 > /dev/null 2>/dev/null &
    PID_XVFB="$!"
    sleep ${SLEEPTIME}
    if kill -0 ${PID_XVFB}; then
        echo "Started on display ${DISPLAYNUM} with pid ${PID_XVFB}"
        XVFB_STARTED=1
    else
        DISPLAYNUM=$((RANDOM%10+90))
        let XVFB_TRIES=${XVFB_TRIES}+1
    fi
done
if [ ! ${XVFB_STARTED} ]; then
    echo "Coult not start xvfb, exiting"
    exit 1
fi

export DISPLAY=:${DISPLAYNUM}

cd ${JSDIR}
${JSDIR}/node_modules/karma/bin/karma start karma.conf.buildserver.js

#if [ "$?" -eq 1 ]; then
#    echo "Error when testing, taking screenshot"
#    import -window root ${WORKSPACE}/test-error.png
#fi

echo "Cleaning up"
kill ${PID_XVFB}
