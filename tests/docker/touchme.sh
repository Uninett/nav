#!/bin/sh -xe
# Sets the mtime of a TARGETFILE to that of the timestamp of the last
# Mercurial changeset that touched HGFILE. Provided mainly to ensure files
# ADDed by Dockerfiles will keep their original timestamps and remain in
# Docker's cache until their contents change.
HGFILE="$1"
TARGETFILE="$2"

# example format: 2014-11-04 14:29 +0100
hgdate=$(hg log -l1 "${HGFILE}" --template '{date|isodate}')

if ! touch -d "${hgdate}" "${TARGETFILE}"; then
    # touch failed. here's an ugly bugly fall back in case the problem is that
    # we are using GNU touch arguments on a BSD touch.
    hgdate=$(echo "$hgdate" | tr -d -- '-: ' | sed 's/[+-].*//')
    touch -t "${hgdate}" "${TARGETFILE}"
fi

