#!/bin/sh -e

# This script will try to determine which installed files have been removed
# between two versions of NAV. It requires all the build prerequisites of both
# versions to be present.

OLDVER="$1"
NEWVER="$2"
test -z "$NEWVER" && NEWVER=tip

if [ -z "$OLDVER" ]; then
    cat <<EOF 
This script will try to determine which installed files have been removed
between two versions of NAV. It requires all the build prerequisites of both
versions to be present.

Usage: whatsgone.sh <oldversion> [<newversion>]
EOF
    exit 1
fi

HG=$(which hg)

if [ -z "$HG" ]; then
    echo "Cannot find a hg executable"
    exit 2
fi

REPO=$($HG root)

if [ -z "$REPO" ]; then
    echo "Not inside a Mercurial repository"
    exit 2
fi

############# now start the good stuff ###############

build() {
    make distclean
    ./autogen.sh
    ./configure
    make
    DESTDIR="$1" make install
}

build_version() {
    local version="$1"
    local DESTDIR="build-$version"
    if [ -d "$DESTDIR" ]; then
	echo "$DESTDIR already exists, not building again"
	return
    fi
    hg up "$version"
    mkdir "$DESTDIR"
    build "$PWD/$DESTDIR"
    (cd "$DESTDIR" && find) | sort | sed 's/^\.//' > "manifest-$version"
}

cd "$REPO"
build_version "$OLDVER"
build_version "$NEWVER"

echo -----
echo "These files appear to have been removed between $OLDVER and $NEWVER:"
echo -----
diff -u "manifest-$OLDVER" "manifest-$NEWVER" | grep '^-' | grep -v '^---' | sed 's/^-//'

