#!/bin/bash
if [ ! -n "$1" ]; then
    echo "Need path to targeturl"
    exit 1
fi

SLEEPTIME=2
export TARGETURL=$1
echo URL ${TARGETURL}

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
fi

export DISPLAY=:${DISPLAYNUM}
python -m functional.geomap.geomap_tests
import -window root ./test-error.png


