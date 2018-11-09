#!/bin/bash
if [ ! -n "$1" ]; then
    echo "Need path to workspace"
    exit 1
fi

WORKSPACE=$1
JSDIR="python/nav/web/static/js"
REPORTDIR="$WORKSPACE/reports"

NPM=`which npm`

cd ${JSDIR}
npm cache clean
npm install

echo "Running jshint"
cd "${WORKSPACE}"
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
jshint --config ${JSDIR}/.jshintrc ${JAVASCRIPT_FILES[@]} --jslint-reporter > "${REPORTDIR}/javascript-jshint.xml" || true

# Verify that jshint was running as jshint will have non-zero exit if ANY linting errors is found.
[ -s "${REPORTDIR}/javascript-jshint.xml" ]

echo "Running tests"
"${JSDIR}/node_modules/karma/bin/karma" start "${JSDIR}/test/karma.conf.buildserver.js"

if [ "$?" -eq 1 ]; then
    echo "Error when testing, taking screenshot"
    import -window root "${REPORTDIR}/javascript-test-error.png"
fi
