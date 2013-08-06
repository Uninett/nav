#!/bin/bash
#
# Starts a virtual framebuffer on a random display between 90 and 99.
#
# As this script uses trap for self cleaning purposes, start it with 'source'
#
SLEEPTIME=2

XVFB=`which Xvfb`
if [ "$?" -eq 1 ]; then
    echo "Xvfb not found"
    exit 1
fi

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
else
    trap 'kill ${PID_XVFB}' EXIT
    export DISPLAY=:${DISPLAYNUM}
fi

