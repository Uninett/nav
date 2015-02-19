#!/bin/bash -x
cd ${WORKSPACE}
cloc \
    --exclude-dir=.env,.idea,tmp,build,doc,htdocs/static/js/libs,htdocs/static/js/node_modules,htdocs/static/js/geomap/projdefs,python/nav/smidumps \
    --exclude-lang=make,m4,XML \
    --not-match-f='(configure|config.status)$' \
    --report-file="${WORKSPACE}/cloc.txt" \
    .

