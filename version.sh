#!/bin/sh
# Update the package version number
HG=`which hg`
VERSION=$1
M4FILE=version.m4

inhgrepo() {
  test -e .hg && test -x "$HG"
}

do_describe() {
  PYTHONPATH=tools ${HG} --config extensions.hgdescribe=tools/hgdescribe describe --single-tag --limit 9999
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

if test -z "$VERSION" && inhgrepo; then
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
