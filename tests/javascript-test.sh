#!/usr/bin/env bash
set -e
if [ ! -n "$1" ]; then
    echo "Need path to workspace"
    exit 1
fi

WORKSPACE="$(realpath $1)"
JSDIR="python/nav/web/static/js"
REPORTDIR="$WORKSPACE/reports"

NPM=`which npm`

cd ${JSDIR}
npm ci

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

# Point to Playwright's Chromium if CHROME_BIN is not already set.
# Playwright's directory layout varies across versions:
#   Old: chromium-<rev>/chrome-linux/chrome, chromium-<rev>/chrome-mac/Chromium.app/...
#   New: chromium-<rev>/chrome-linux-x64/chrome, chromium-<rev>/chrome-mac-arm64/Google Chrome for Testing.app/...
# PLAYWRIGHT_BROWSERS_PATH may override the default cache location (e.g. in devcontainers).
if [[ -z "$CHROME_BIN" ]]; then
    PLAYWRIGHT_CHROME=$(find \
        ${PLAYWRIGHT_BROWSERS_PATH:+"$PLAYWRIGHT_BROWSERS_PATH"} \
        "$HOME/.cache/ms-playwright" \
        "$HOME/Library/Caches/ms-playwright" \
        "$WORKSPACE/.cache/ms-playwright" \
        \( -path "*/chromium-*/chrome-linux*/chrome" \
           -o \( -path "*/chromium-*/chrome-mac*/*.app/Contents/MacOS/*" \
                 ! -path "*/Helpers/*" ! -path "*/Frameworks/*" \) \) \
        2>/dev/null | sort -Vr | head -1)
    [[ -n "$PLAYWRIGHT_CHROME" ]] && export CHROME_BIN="$PLAYWRIGHT_CHROME"
fi

"${JSDIR}/node_modules/karma/bin/karma" start "${JSDIR}/test/karma.conf.buildserver.js"
