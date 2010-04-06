#!/bin/sh
# Update the package version number
HG=`which hg`
VERSION=$1

inhgrepo() {
  test -e .hg && test -x "$HG"
}

do_describe() {
  PYTHONPATH=tools ${HG} --config extensions.hgdescribe=tools/hgdescribe describe --single-tag
}
if test -z "$VERSION" && inhgrepo; then
  VERSION=`do_describe`
fi

if test -n "$VERSION"; then
  echo "m4_define([VERSION_NUMBER], [${VERSION}])" > version.m4
  echo "Updated version number to ${VERSION}"
else 
  echo "Cannot update version number."
  exit 1
fi
