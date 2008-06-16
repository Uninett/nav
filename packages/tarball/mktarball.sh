#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo Must have destination tarball name as argument
    exit 1
fi

TARBALL="$1"
BUILD_ROOT=~/tmp/NAVBUILD
_prefix=/usr/local/nav

# Clear stuff out of the way
rm ${TARBALL}
rm -rf ${BUILD_ROOT}
echo Creating build root at ${BUILD_ROOT}
mkdir -p ${BUILD_ROOT}

# Build the thing
echo Building...
autoconf
./configure --prefix=${_prefix}
make
make DESTDIR=${BUILD_ROOT} install

# Grab some extra files that aren't part of the build yet
extra=`find bin/ -name '*.sh'`
for file in $extra
do
  install -v -m 755 -D $file ${BUILD_ROOT}${_prefix}/$file
done

# Some chmod fixes
chmod g+w ${BUILD_ROOT}${_prefix}/etc/*
chmod 755 ${BUILD_ROOT}${_prefix}/etc/init.d/*


# Tarball it
oldwd=$PWD
cd ${BUILD_ROOT}${_prefix}
tar cvzf ${TARBALL} --owner=root --group=nav *
mv ${TARBALL} $oldwd
echo "Tarball created ($TARBALL)"
