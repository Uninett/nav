#!/bin/sh
mydir="$(dirname $0)"

exec "${mydir}/dump-remote-db.sh" "$@" | "${mydir}/restore-db.sh"
