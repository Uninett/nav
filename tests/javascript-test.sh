#!/bin/bash
if [ ! -n "$1" ]; then
    echo "Need path to workspace"
    exit 1
fi

WORKSPACE=$1
JSDIR="${WORKSPACE}/media/js"

XVFB=`which Xvfb`
if [ "$?" -eq 1 ]; then
    echo "Xvfb not found"
    exit 1
fi

BUSTERSERVER=`which buster-server`
if [ "$?" -eq 1 ]; then
    echo "buster-server not found"
    exit 1
fi

BUSTERTEST=`which buster-test`
if [ "$?" -eq 1 ]; then
    echo "buster-test not found"
    exit 1
fi

GOOGLECHROME=`which google-chrome`
if [ "$?" -eq 1 ]; then
    echo "google chrome not found"
    exit 1
fi

# Buster-amd is required, check if it's installed locally
if [ ! -d "${JSDIR}/node_modules/buster-amd" ]; then
    NPM=`which npm`
    if [ "$?" -eq 1 ]; then
        echo "No buster-amd and no npm, need both"
        exit 1
    fi
    cd ${JSDIR}
    echo "Installing buster-amd locally"
    npm install buster-amd
fi

echo "Starting Xvfb"
XVFB_TRIES=0
XVFB_STARTED=0
until [ ${XVFB_STARTED} -eq 1 ] || (( ${XVFB_TRIES} > 10 )) ; do
    # Find random display number for Xvfb
    DISPLAYNUM=$((RANDOM%10+90))
    ${XVFB} :${DISPLAYNUM} > /dev/null 2>/dev/null &
    PID_XVFB="$!"
    sleep 4
    if jobs | grep XVFB; then
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

echo "Starting buster-server"
BUSTER_TRIES=0
BUSTER_STARTED=0
until [ ${BUSTER_STARTED} -eq 1 ] || (( ${BUSTER_TRIES} > 10 )) ; do
    # Find random port for buster-server
    BUSTERPORT=$((RANDOM%100+1200))
    ${BUSTERSERVER} -l error -p ${BUSTERPORT} &
    PID_BUSTER="$!"
    sleep 4
    if jobs | grep BUSTERSERVER; then
        echo "Started on port ${BUSTERPORT} with pid ${PID_BUSTER}"
        BUSTER_STARTED=1
    else
        BUSTERPORT=$((RANDOM%100+1200))
        let BUSTER_TRIES=${BUSTER_TRIES}+1
    fi
done

if [ ! ${BUSTER_STARTED} ]; then
    echo "Could not start buster-server, exiting"
    kill ${PID_XVFB}
    exit 1
fi

echo "Starting Google Chrome"
export DISPLAY=:${DISPLAYNUM}
${GOOGLECHROME} http://localhost:${BUSTERPORT}/capture &
PID_CHROME="$!"
echo "Started on display ${DISPLAYNUM} with pid ${PID_CHROME} connected to ${BUSTERPORT}"
sleep 4

echo "Running tests"
cd ${WORKSPACE}/media/js
${BUSTERTEST} -s http://localhost:${BUSTERPORT} -r xml > ${WORKSPACE}/tests/javascript-result.xml

sleep 1

echo "Cleaning up"
kill ${PID_CHROME}
sleep 1
kill ${PID_XVFB}
kill ${PID_BUSTER}
