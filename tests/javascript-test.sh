#!/bin/bash
if [ ! -n "$1" ]; then
    echo "Need path to workspace"
    exit 1
fi

WORKSPACE=$1
JSDIR="${WORKSPACE}/htdocs/static/js"


NPM=`which npm`

cd ${JSDIR}
npm cache clean
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
jshint --config ${JSDIR}/.jshintrc ${JAVASCRIPT_FILES[@]} --jslint-reporter > ${JSDIR}/javascript-jshint.xml || true

# Verify that jshint was running as jshint will have non-zero exit if ANY linting errors is found.
[ -s "${JSDIR}/javascript-jshint.xml" ]

echo "Running tests"
cd ${JSDIR}
${JSDIR}/node_modules/.bin/karma start test/karma.conf.buildserver.js

if [ "$?" -eq 1 ]; then
    echo "Error when testing, taking screenshot"
    import -window root ${WORKSPACE}/test-error.png
fi
