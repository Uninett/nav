#!/bin/sh
# Update the package version number
GIT=`which git`
VERSION=$1
M4FILE=version.m4

ingitrepo() {
  test -e .git && test -x "$GIT"
}

do_describe() {
  ${GIT} describe --tags
}

get_version() {
  if [ -f ${M4FILE} ]; then
    m4 -P ${M4FILE} - <<EOF
VERSION_NUMBER
EOF
  else
    echo unknown
  fi
}

if test -z "$VERSION" && ingitrepo; then
  VERSION=`do_describe`
fi

if test -n "$VERSION"; then
  echo "m4_define(VERSION_NUMBER, ${VERSION})" > ${M4FILE}
  echo "Updated version number to ${VERSION}"
else
  VERSION=$(get_version | tr -d "\n")
  echo "Keeping version number: ${VERSION}"
  exit 1
fi
