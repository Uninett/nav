#!/bin/bash -x
cd ${WORKSPACE}
cloc \
    --exclude-list-file=tests/.clocignore \
    --exclude-lang=make,m4,XML \
    --not-match-f='(configure|config.status)$' \
    --by-file \
    --xml \
    --out="${WORKSPACE}/cloc.xml" \
    .
