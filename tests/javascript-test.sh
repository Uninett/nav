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

GOOGLECHROME=`which google-chrome`
if [ "$?" -eq 1 ]; then
    echo "google chrome not found"
    exit 1
fi

NPM=`which npm`

# Function to check for module
# Will trigger npmInstall if not found.
function npmModule {
    if [ -z "$1" ]; then
        echo "Need to specify module to check for..."
        exit 1
    else
        if [ ! -d "${JSDIR}/node_modules/${1}" ]; then
            npmInstall $1
        fi
    fi
}

# Tries to install a module from NPM
function npmInstall {
        if [ -z "${NPM}" ]; then
            echo "No $1 and no npm, need both"
            exit 1
        else
            cd ${JSDIR}
            echo "Trying to install $1 locally"
            npm install $1
            if [ "$?" -ne 0 ]; then
                echo "Failed to install $1"
                exit 1
            else
                echo "Installed $1"
            fi
        fi
}

#  This requires to be installed global as you want buster in PATH :-(
#npmModule buster

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

npmModule buster-amd
npmModule jshint


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

echo "Starting buster-server"
BUSTER_TRIES=0
BUSTER_STARTED=0
until [ ${BUSTER_STARTED} -eq 1 ] || (( ${BUSTER_TRIES} > 10 )) ; do
    # Find random port for buster-server
    BUSTERPORT=$((RANDOM%100+1200))
    ${BUSTERSERVER} -l error -p ${BUSTERPORT} &
    PID_BUSTER="$!"
    sleep ${SLEEPTIME}
    if kill -0 ${PID_BUSTER}; then
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
sleep ${SLEEPTIME}

echo "Running tests"
cd ${WORKSPACE}/media/js
${BUSTERTEST} -s http://localhost:${BUSTERPORT} -r xml > ${WORKSPACE}/tests/javascript-results.xml

if [ "$?" -eq 1 ]; then
    echo "Error when testing, taking screenshot"
    import -window root ${WORKSPACE}/test-error.png
fi

echo "Cleaning up"
kill ${PID_CHROME}
sleep 1
kill ${PID_XVFB}
kill ${PID_BUSTER}
