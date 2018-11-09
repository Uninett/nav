#!/bin/bash -x
cd "${WORKSPACE}"
cloc \
    --list-file=tests/.clocinclude \
    --exclude-list-file=tests/.clocignore \
    --exclude-lang=make,m4,XML \
    --by-file \
    --xml \
    --out="${WORKSPACE}/reports/cloc.xml" \
    .
